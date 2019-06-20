"""Event handlers for Server types & its components (PSU)
There're 2 server types - with and without IPMI/BMC support;
Both server types have a unique VM (domain) assigned to them
"""
# **due to circuit callback signature
# pylint: disable=W0613

import os
import time
import logging
import math
import operator
from threading import Thread

from circuits import handler

from enginecore.state.hardware.static_asset import StaticAsset
from enginecore.state.api.state import IStateManager

from enginecore.state.hardware.asset_definition import register_asset
import enginecore.state.hardware.internal_state as in_state

from enginecore.state.agent import IPMIAgent, StorCLIEmulator
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.state_initializer import get_temp_workplace_dir
from enginecore.state.hardware import event_results


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

    def _get_server_load_update(self, volt_event_details, power_e_result=None):
        """Get formatted load event result 
        (load update that needs to be propagated up the power stream)
        """

        load_e_results = []

        old_volt, new_volt = (
            volt_event_details["old_value"],
            volt_event_details["new_value"],
        )
        src_key = volt_event_details["source_key"]

        source_psu = self._psu_sm[src_key]

        calc_load = lambda v: (self.state.power_consumption / v if v else 0)

        # Output voltage can still be 0 for some assets even though
        # their input voltage > 0
        # (most devices require at least 90V-100V in order to function)
        old_out_volt = old_volt * (power_e_result.old_state if power_e_result else 1)
        new_out_volt = new_volt * (power_e_result.new_state if power_e_result else 1)

        old_load, new_load = (calc_load(volt) for volt in [old_out_volt, new_out_volt])

        if old_load == new_load == 0:
            return None

        other_psu = [self._psu_sm[k] for k in self._psu_sm if k != src_key]
        print("\n=" * 10)
        print("VOLT UPDATE SERVER: PRINTING PSUS")
        print(other_psu[0])
        print(source_psu)

        _2nd_parent = other_psu[0]
        load_change = old_load - new_load

        load_e_results.append(
            event_results.LoadEventResult(
                asset_key=self.state.key,
                asset_type=self.state.asset_type,
                parent_key=source_psu.key,
                old_load=old_load,
                new_load=new_load * source_psu.draw_percentage,
            )
        )

        # Case where load re-distribution is not needed
        if (
            _2nd_parent.load
            == calc_load(_2nd_parent.output_voltage) * _2nd_parent.draw_percentage
        ) and math.isclose(old_load, 0):
            print("Other PSU drawing as expected")
            return load_e_results

        if math.isclose(new_out_volt, 0) and _2nd_parent.status:
            print("LOAD REDISTRIBUTION NEEDED!!!" * 3)
            load_e_results.append(
                event_results.LoadEventResult(
                    asset_key=self.state.key,
                    asset_type=self.state.asset_type,
                    parent_key=source_psu.key,
                    old_load=source_psu.load,
                    new_load=new_load * source_psu.draw_percentage,
                )
            )
            # return load_e_results

        print("=\n" * 10)

        print(load_e_results)
        print("=\n" * 10)

        return load_e_results

    @handler("VoltageIncreased")
    def on_voltage_increase(self, event, *args, **kwargs):
        """Handle input power voltage increase"""

        power_event_result = None

        volt_event_result = self._get_voltage_event_result(kwargs)
        load_event_result = self._get_server_load_update(kwargs)

        return volt_event_result, power_event_result, load_event_result

    @handler("VoltageDecreased")
    def on_voltage_decrease(self, event, *args, **kwargs):
        """Handle input power voltage drop"""

        power_event_result = None

        volt_event_result = self._get_voltage_event_result(kwargs)
        load_event_result = self._get_server_load_update(kwargs)

        return volt_event_result, power_event_result, load_event_result


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
        logging.info(self._ipmi_agent)

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
                    logging.info(cpu_i)

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

    @handler("AmbientDecreased", "AmbientIncreased")
    def on_ambient_updated(self, event, *args, **kwargs):
        """Update thermal sensor readings on ambient changes """
        self._sensor_repo.adjust_thermal_sensors(
            new_ambient=kwargs["new_value"], old_ambient=kwargs["old_value"]
        )
        self.state.update_storage_temperature(
            new_ambient=kwargs["new_value"], old_ambient=kwargs["old_value"]
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
