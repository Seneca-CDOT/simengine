"""Event handlers for Server types & its components (PSU)
There're 2 server types - with and without IPMI/BMC support;
Both server types have a unique VM (domain) assigned to them
"""
# **due to circuit callback signature
# pylint: disable=W0613

import os
import time
import logging
import operator
import math
from threading import Thread

from circuits import handler

from enginecore.state.hardware.static_asset import StaticAsset
from enginecore.state.api.state import IStateManager

from enginecore.state.hardware.asset_definition import register_asset
import enginecore.state.hardware.internal_state as in_state

from enginecore.state.agent import IPMIAgent, StorCLIEmulator
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.state_initializer import get_temp_workplace_dir
from enginecore.state.engine.events import EventDataPair

logger = logging.getLogger(__name__)


@register_asset
class Server(StaticAsset):
    """Asset controlling a VM (without IPMI support)"""

    channel = "engine-server"
    StateManagerCls = in_state.ServerStateManager

    def __init__(self, asset_info):
        super(Server, self).__init__(asset_info)
        self._psu_sm = {}

        for i in range(1, asset_info["num_components"] + 1):
            psu_key = self.key * 10 + i
            self._psu_sm[psu_key] = IStateManager.get_state_manager_by_key(psu_key)

        self.state.power_up()

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        asset_event = event.get_next_power_event(self)
        assert event.source_key in self._psu_sm

        e_src_psu = self._psu_sm[event.source_key]

        # keep track of load udpates for multi-psu servers
        load_upd = {}
        extra_draw = 0.0
        load_should_change = True

        drawing_extra = (
            lambda x: asset_event.calculate_load(self.state, x.input_voltage)
            * x.draw_percentage
            < x.load
        )

        new_asset_load = asset_event.calculate_load(self.state, event.in_volt.new)
        old_asset_load = asset_event.calculate_load(self.state, event.in_volt.old)

        # initialize load for PSUs (as unchaned)
        for key in self._psu_sm:
            psu_sm = self._psu_sm[key]

            load_upd[key] = EventDataPair(psu_sm.load, psu_sm.load)
            # if alternative power source is off, grab extra load from it
            if psu_sm.key != event.source_key and not psu_sm.status:
                extra_draw += psu_sm.draw_percentage

            # if alternative power source is currently having extra load
            # that the volt event source asset is supposed to be drawing
            elif (
                psu_sm.key != event.source_key
                and math.isclose(event.in_volt.old, 0.0)
                and drawing_extra(psu_sm)
            ):
                # asset load should not change (we are just redistributing same load)
                load_upd[key].new = (
                    load_upd[key].old - new_asset_load * e_src_psu.draw_percentage
                )
                load_should_change = False

        src_psu_draw = e_src_psu.draw_percentage + extra_draw
        load_upd[e_src_psu.key].old = old_asset_load * src_psu_draw
        load_upd[e_src_psu.key].new = new_asset_load * src_psu_draw

        # power up if server is offline
        if not asset_event.state.old:
            asset_event.state.new = self.state.power_up()

        asset_event.streamed_load_updates = load_upd
        if load_should_change:
            asset_event.calc_load_from_volt()
            self._update_load(self.state.load + load_upd[e_src_psu.key].difference)

        return asset_event

    @handler("InputVoltageDownEvent")
    def on_input_voltage_down(self, event, *args, **kwargs):
        asset_event = event.get_next_power_event(self)
        assert event.source_key in self._psu_sm

        # store state info of the PSU causing havoc, keep track
        # of alternative power sources
        e_src_psu = self._psu_sm[event.source_key]
        e_src_psu_offline = math.isclose(event.in_volt.new, 0.0)

        alt_power_present = False

        # keep track of load udpates for multi-psu servers
        load_upd = {}

        # initialize load for PSUs (as unchaned)
        for key in self._psu_sm:
            load_upd[key] = EventDataPair(
                self._psu_sm[key].load, self._psu_sm[key].load
            )

        load_upd[e_src_psu.key].new = (
            asset_event.calculate_load(self.state, event.in_volt.new)
            * e_src_psu.draw_percentage
        )

        # check alternative power sources
        # and leave this server online if present
        for psu_key in self._psu_sm:
            psu_sm = self._psu_sm[psu_key]
            if psu_key != e_src_psu.key and psu_sm.status:
                alt_power_present = True
                if e_src_psu_offline:
                    load_upd[psu_key].new = (
                        load_upd[psu_key].new - load_upd[e_src_psu.key].difference
                    )

        # state needs to change when all power sources are offline
        if not alt_power_present:
            asset_event.state.new = self.state.power_off()

        # update server load if all PSUs are off or
        # if in voltage simply dropped (but not to zero)
        if not alt_power_present or not e_src_psu_offline:
            asset_event.calc_load_from_volt()
            self._update_load(self.state.load + load_upd[e_src_psu.key].difference)

        asset_event.streamed_load_updates = load_upd

        return asset_event


@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI and StorCLI support"""

    channel = "engine-bmc"
    StateManagerCls = in_state.BMCServerStateManager

    def __init__(self, asset_info):
        super(ServerWithBMC, self).__init__(asset_info)

        # create state directory
        ipmi_dir = os.path.join(get_temp_workplace_dir(), str(asset_info["key"]))
        os.makedirs(ipmi_dir)

        self._sensor_repo = SensorRepository(asset_info["key"], enable_thermal=True)

        # set up agents
        ipmi_conf = {
            k: asset_info[k] for k in asset_info if k in IPMIAgent.lan_conf_attributes
        }
        self._ipmi_agent = IPMIAgent(ipmi_dir, ipmi_conf, self._sensor_repo)
        self._storcli_emu = StorCLIEmulator(
            asset_info["key"], ipmi_dir, socket_port=asset_info["storcliPort"]
        )

        self.state.update_agent(self._ipmi_agent.pid)
        logger.info(self._ipmi_agent)

        self.state.update_cpu_load(0)
        self._cpu_load_t = None
        self._launch_monitor_cpu_load()

    def _launch_monitor_cpu_load(self):
        """Start a thread that will decrease battery level """

        # launch a thread
        self._cpu_load_t = Thread(
            target=self._monitor_load, name="cpu_load:{}".format(self.key)
        )

        self._cpu_load_t.daemon = True
        self._cpu_load_t.start()

    def _monitor_load(self):
        """Sample cpu load every 5 seconds """

        cpu_time_1 = 0
        sample_rate_sec = 5

        # get the delta between two samples
        ns_to_sec = lambda x: x / 1e9
        calc_cpu_load = lambda t1, t2: min(
            100 * (abs(ns_to_sec(t2) - ns_to_sec(t1)) / sample_rate_sec), 100
        )

        while True:
            if self.state.status and self.state.vm_is_active():

                # more details on libvirt api:
                # https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirt
                cpu_stats = self.state.get_cpu_stats()[0]
                cpu_time_2 = cpu_stats["cpu_time"] - (
                    cpu_stats["user_time"] + cpu_stats["system_time"]
                )

                if cpu_time_1:
                    self.state.update_cpu_load(calc_cpu_load(cpu_time_1, cpu_time_2))
                    cpu_i = "server[{0.key}] CPU load:{0.cpu_load}%".format(self.state)
                    logger.debug(cpu_i)

                cpu_time_1 = cpu_time_2
            else:
                cpu_time_1 = 0
                self.state.update_cpu_load(0)

            time.sleep(sample_rate_sec)

    def add_sensor_thermal_impact(self, source, target, event):
        """Add new thermal relationship at the runtime"""
        self._sensor_repo.get_sensor_by_name(source).add_sensor_thermal_impact(
            target, event
        )

    def add_cpu_thermal_impact(self, target):
        """Add new thermal cpu load & sensor relationship"""
        self._sensor_repo.get_sensor_by_name(target).add_cpu_thermal_impact()

    def add_storage_cv_thermal_impact(self, source, controller, cache_v, event):
        """Add new sensor & cachevault thermal relationship
        Args:
            source(str): name of the source sensor causing thermal changes
            cache_v(str): serial number of the cachevault
        """
        sensor = self._sensor_repo.get_sensor_by_name(source)
        sensor.add_cv_thermal_impact(controller, cache_v, event)

    def add_storage_pd_thermal_impact(self, source, controller, drive, event):
        """Add new sensor & physical drive thermal relationship
        Args:
            source(str): name of the source sensor causing thermal changes
            drive(int): serial number of the cachevault
        """
        sensor = self._sensor_repo.get_sensor_by_name(source)
        sensor.add_pd_thermal_impact(controller, drive, event)

    @handler("AmbientUpEvent", "AmbientDownEvent")
    def on_ambient_updated(self, event, *args, **kwargs):
        """Update thermal sensor readings on ambient changes """
        self._sensor_repo.adjust_thermal_sensors(
            new_ambient=event.temperature.new, old_ambient=event.temperature.old
        )
        self.state.update_storage_temperature(
            new_ambient=event.temperature.new, old_ambient=event.temperature.old
        )

    def on_power_off_request_received(self, event, *args, **kwargs):
        self._ipmi_agent.stop_agent()
        e_result = self.power_off()
        if e_result.old_state != e_result.new_state:
            self._sensor_repo.shut_down_sensors()
        return e_result

    def on_power_up_request_received(self, event, *args, **kwargs):
        self._ipmi_agent.start_agent()
        e_result = self.power_up()
        if e_result.old_state != e_result.new_state:
            self._sensor_repo.power_up_sensors()
        return e_result

    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        """Set sensors to off values on power down (no power source)"""
        self._sensor_repo.shut_down_sensors()

    @handler("ButtonPowerUpPressed")
    def on_asset_did_power_on(self):
        """Update senosrs on power online"""
        self._sensor_repo.power_up_sensors()


@register_asset
class PSU(StaticAsset):
    """PSU """

    channel = "engine-psu"
    StateManagerCls = in_state.PSUStateManager

    def __init__(self, asset_info):
        super(PSU, self).__init__(asset_info)

        # only ServerWithBmc needs to handle events (in order to update sensors)
        if "Server" in asset_info["children"][0].labels:
            self.removeHandler(self.on_asset_did_power_off)
            self.removeHandler(self.on_asset_did_power_on)
            self.removeHandler(self.increase_load_sensors)
            self.removeHandler(self.decrease_load_sensors)
        else:
            self._sensor_repo = SensorRepository(
                str(asset_info["key"])[:-1], enable_thermal=True
            )
            self._psu_sensor_names = self._state.get_psu_sensor_names()

    def _set_psu_status(self, value):
        """Update psu status if sensor is supported"""
        if "psuStatus" in self._psu_sensor_names:
            psu_status = self._sensor_repo.get_sensor_by_name(
                self._psu_sensor_names["psuStatus"]
            )
            psu_status.sensor_value = value

    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        """PSU status was set to failed"""
        self._set_psu_status("0x08")

    @handler("ButtonPowerUpPressed")
    def on_asset_did_power_on(self):
        """PSU was brought back up"""
        self._set_psu_status("0x01")

    def _update_load_sensors(self, load, arith_op):
        """Update psu sensors associated with load
        Args:
            load: amperage change
            arith_op(operator): operation on old & new load to be performed
        """

        if "psuCurrent" in self._psu_sensor_names:
            psu_current = self._sensor_repo.get_sensor_by_name(
                self._psu_sensor_names["psuCurrent"]
            )

            psu_current.sensor_value = int(arith_op(self._state.load, load))

        if "psuPower" in self._psu_sensor_names:
            psu_current = self._sensor_repo.get_sensor_by_name(
                self._psu_sensor_names["psuPower"]
            )

            psu_current.sensor_value = int((arith_op(self._state.load, load)) * 10)

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased", priority=1)
    def increase_load_sensors(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        """
        self._update_load_sensors(kwargs["child_load"], operator.add)

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased", priority=1)
    def decrease_load_sensors(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        """
        self._update_load_sensors(kwargs["child_load"], operator.sub)
