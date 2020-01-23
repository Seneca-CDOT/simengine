"""Event handlers for Server types & its components (PSU)
There're 2 server types - with and without IPMI/BMC support;
Both server types have a unique VM (domain) assigned to them
"""
# **due to circuit callback signature
# pylint: disable=W0613

import logging
import operator
import math
from threading import Thread, Event

from circuits import handler

from enginecore.state.hardware.static_asset import StaticAsset
from enginecore.state.api.state import IStateManager

from enginecore.state.hardware.asset_definition import register_asset
import enginecore.state.hardware.internal_state as in_state

from enginecore.state.agent import IPMIAgent, StorCLIEmulator
from enginecore.state.sensor.repository import SensorRepository
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
        self._storcli_emu = None
        self.removeHandler(super().on_power_button_press)

        for i in range(1, asset_info["num_components"] + 1):
            psu_key = self.key * 10 + i
            self._psu_sm[psu_key] = IStateManager.get_state_manager_by_key(psu_key)

        if "storcliEnabled" in asset_info and asset_info["storcliEnabled"]:
            server_dir = self._create_asset_workplace_dir()

            self._storcli_emu = StorCLIEmulator(
                asset_info["key"], server_dir, socket_port=asset_info["storcliPort"]
            )

        self.state.power_up()

    def _psu_out_voltage(self):
        """Find server input voltage
        (by finding a psu powering this asset that outputs voltage)
        """
        for key in self._psu_sm:
            if self._psu_sm[key].status:
                return self._psu_sm[key].output_voltage
        return 0.0

    def _psu_drawing_extra(self, psu_sm):
        """Check if a particular psu is drawing extra power
        Returns:
            boolean: True if psu is drawing above the expected value 
                     (meaning it is taking over someone else's load)
        """

        calc_load = lambda consumption, voltage: consumption / voltage if voltage else 0

        psu_draw = (
            calc_load(self.state.power_consumption, psu_sm.input_voltage)
            * psu_sm.draw_percentage
        )
        psu_draw += calc_load(psu_sm.power_consumption, psu_sm.input_voltage)

        return psu_draw < psu_sm.load

    @handler("PowerButtonOffEvent")
    def on_power_button_off(self, event, *args, **kwargs):
        """React to server shut down by setting up upstream load for
        server PSUs"""
        asset_event = event.get_next_power_event()
        load_upd = {}

        asset_event.load.new = asset_event.calculate_load(
            self.state, self.state.input_voltage
        )

        for key in self._psu_sm:
            psu_sm = self._psu_sm[key]

            load_upd[key] = EventDataPair(psu_sm.load, psu_sm.load)
            if not psu_sm.status or math.isclose(psu_sm.input_voltage, 0.0):
                continue

            load_upd[key].new = psu_sm.power_usage

        asset_event.streamed_load_updates = load_upd
        return asset_event

    @handler("PowerButtonOnEvent")
    def on_power_button_on(self, event, *args, **kwargs):
        """React to power button event by notifying engine of
        state changes associated with it"""

        asset_event = event.get_next_power_event()
        load_upd = {}
        extra_draw = 0.0
        online_psus = []

        asset_event.load.new = asset_event.calculate_load(
            self.state, self.state.input_voltage
        )

        # for each psu, check if
        for key in self._psu_sm:
            psu_sm = self._psu_sm[key]

            load_upd[key] = EventDataPair(psu_sm.load, psu_sm.load)
            if not psu_sm.status:
                extra_draw += psu_sm.draw_percentage
            else:
                load_upd[key].new = (
                    load_upd[key].new + asset_event.load.new * psu_sm.draw_percentage
                )
                online_psus.append(key)

        extra_load = asset_event.load.new * extra_draw / len(online_psus)

        for key in online_psus:
            load_upd[key].new = load_upd[key].new + extra_load

        asset_event.streamed_load_updates = load_upd
        return asset_event

    @handler("InputVoltageUpEvent", "InputVoltageDownEvent", priority=10)
    def detect_input_voltage(self, event, *args, **kwargs):
        """Update input voltage
        (called after every other handler due to priority set to -1)
        """
        self.state.update_input_voltage(max(self._psu_out_voltage(), event.in_volt.new))

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        asset_event = event.get_next_power_event(self)
        assert event.source_key in self._psu_sm

        e_src_psu = self._psu_sm[event.source_key]

        # keep track of load updates for multi-psu servers
        load_upd = {}
        extra_draw = 0.0

        should_change_load = True
        should_power_up = (
            not self.state.status or not self.state.vm_is_active()
        ) and not math.isclose(event.in_volt.new, 0.0)

        new_asset_load = asset_event.calculate_load(self.state, event.in_volt.new)
        old_asset_load = asset_event.calculate_load(self.state, event.in_volt.old)

        # initialize load for PSUs
        # and process alternative power sources (PSUs)
        for key in self._psu_sm:

            psu_sm = self._psu_sm[key]
            load_upd[key] = EventDataPair(0.0, 0.0)

            if psu_sm.key == event.source_key:
                continue

            # if alternative power source is off, grab extra load from it
            if not psu_sm.status:
                extra_draw += psu_sm.draw_percentage

            # if alternative power source is currently having extra load
            # that the volt event source asset is supposed to be drawing
            # then redistribute it back so that load is equal among all psus
            elif math.isclose(event.in_volt.old, 0.0) and self._psu_drawing_extra(
                psu_sm
            ):
                # asset load should not change (we are just redistributing same load)
                load_upd[key].old = psu_sm.load
                load_upd[key].new = (
                    psu_sm.load - new_asset_load * e_src_psu.draw_percentage
                )
                should_change_load = False
            # add load to a psu due to server powering up
            elif should_power_up:
                load_upd[psu_sm.key].new = new_asset_load * psu_sm.draw_percentage

        # set load for the PSU voltage event is associated with
        src_psu_draw = e_src_psu.draw_percentage + extra_draw
        load_upd[e_src_psu.key].old = old_asset_load * src_psu_draw
        load_upd[e_src_psu.key].new = new_asset_load * src_psu_draw

        # power up if server is offline & boot-on-power BIOS option is on
        if should_power_up and self.state.power_on_ac_restored:
            asset_event.state.new = self.power_up()
            self._update_load(self.state.power_consumption / event.in_volt.new)

        # update load if no state changes
        elif not should_power_up and should_change_load:
            asset_event.calc_load_from_volt()
            self._update_load(self.state.load + load_upd[e_src_psu.key].difference)
        elif not self.state.status and not self.state.power_on_ac_restored:
            load_upd = {}

        asset_event.streamed_load_updates = load_upd
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

        if not math.isclose(
            self.state.load * e_src_psu.draw_percentage, e_src_psu.load
        ):
            source_psu_own_load = asset_event.calculate_load(
                e_src_psu, event.in_volt.old
            )
        else:
            source_psu_own_load = 0

        # keep track of load updates for multi-psu servers
        load_upd = {}

        # initialize load for PSUs (as unchanged)
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

            # skip over source event psu or offline psus
            if psu_key == e_src_psu.key or not psu_sm.status:
                continue

            alt_power_present = True
            # no load redistribution happens if source is still online
            if not e_src_psu_offline:
                continue

            # distribute load to another PSU
            load_upd[psu_key].new = (
                load_upd[psu_key].new
                - load_upd[e_src_psu.key].difference
                - source_psu_own_load
            )

        # finalize asset state changes based off PSU and in-volt status
        if not alt_power_present and e_src_psu_offline:
            # state needs to change when all power sources are offline
            asset_event.state.new = self.power_off()

        # update server load if all PSUs are off or
        # if in voltage simply dropped (but not to zero)
        if not alt_power_present or not e_src_psu_offline:
            asset_event.calc_load_from_volt()
            self._update_load(self.state.load + load_upd[e_src_psu.key].difference)

        asset_event.streamed_load_updates = load_upd

        return asset_event

    def stop(self, code=None):
        if self._storcli_emu is not None:
            self._storcli_emu.stop_server()
        super().stop(code)


@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI and StorCLI support"""

    channel = "engine-bmc"
    StateManagerCls = in_state.BMCServerStateManager

    def __init__(self, asset_info):
        super(ServerWithBMC, self).__init__(asset_info)

        server_dir = self._create_asset_workplace_dir()
        self._stop_event = Event()

        self._sensor_repo = SensorRepository(asset_info["key"], enable_thermal=True)

        # set up agents
        ipmi_conf = {
            k: asset_info[k] for k in asset_info if k in IPMIAgent.lan_conf_attributes
        }

        self._ipmi_agent = IPMIAgent(server_dir, ipmi_conf, self._sensor_repo)
        self.state.update_agent(self._ipmi_agent.pid)
        logger.info(self._ipmi_agent)

        self.state.update_cpu_load(0)
        self._vm_monitor_t = None
        self._launch_monitor_vm()

    def _launch_monitor_vm(self):
        """Start vm monitoring in a thread"""

        # launch a thread
        self._vm_monitor_t = Thread(
            target=self._monitor_vm, name="vm-tracker:{}".format(self.key)
        )

        self._vm_monitor_t.daemon = True
        self._vm_monitor_t.start()

    def _monitor_vm(self):
        """Samples cpu load every 5 seconds, detects changes to VM state
        that occur outside of engine's control
        & notifies main event loop of power update.
        Note that this only tracks down when a vm is powered off.
        
        This method should be run in a thread,
        monitoring can be stopped by setting stop event;
        """

        cpu_time_1 = 0
        sample_rate_sec = 5

        # get the delta between two samples
        # nanoseconds to seconds
        ns_to_sec = lambda x: x / 1e9
        calc_cpu_load = lambda t1, t2: min(
            100 * (abs(ns_to_sec(t2) - ns_to_sec(t1)) / sample_rate_sec), 100
        )

        while not self._stop_event.is_set():

            # get a sample of CPU load if vm is up & running
            if self.state.status and self.state.vm_is_active():

                # more details on libvirt api:
                # https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirt
                cpu_stats = self.state.get_cpu_stats()[0]
                cpu_time_2 = cpu_stats["cpu_time"] - (
                    cpu_stats["user_time"] + cpu_stats["system_time"]
                )

                # skip if first sample is not set yet
                if cpu_time_1:
                    self.state.update_cpu_load(calc_cpu_load(cpu_time_1, cpu_time_2))
                    cpu_i = "server[{0.key}] CPU load:{0.cpu_load}%".format(self.state)
                    logger.debug(cpu_i)

                cpu_time_1 = cpu_time_2

            # either VM is offline or hardware asset status is off
            else:
                # detect state changes happening outside of simengine
                # (for example, if someone powers off vm manually)
                if self.state.status and not self.state.vm_is_active():
                    self.state.publish_power(old_state=1, new_state=0)

                cpu_time_1 = 0
                self.state.update_cpu_load(0)

            self._stop_event.wait(sample_rate_sec)

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

        return event

    def power_off(self, state_reason=None):
        old_state = self.state.status
        new_state = super().power_off(state_reason)

        if old_state != new_state:
            self._sensor_repo.shut_down_sensors()
        return new_state

    def power_up(self, state_reason=None):
        old_state = self.state.status
        new_state = super().power_up(state_reason)

        if old_state != new_state:
            self._sensor_repo.power_up_sensors()
        return new_state

    @handler("PowerButtonOffEvent")
    def on_asset_did_power_off(self, event, *args, **kwargs):
        """Set sensors to off values on power down (no power source)"""
        self._sensor_repo.shut_down_sensors()

    @handler("PowerButtonOnEvent")
    def on_asset_did_power_on(self, event, *args, **kwargs):
        """Update sensors on power online"""
        self._sensor_repo.power_up_sensors()

    def stop(self, code=None):
        self._ipmi_agent.stop_agent()
        self._sensor_repo.stop()
        self._stop_event.set()

        if self._vm_monitor_t is not None and self._vm_monitor_t.isAlive():
            self._vm_monitor_t.join()

        super().stop(code)

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        if not self._ipmi_agent.process_running():
            logger.debug("Starting IPMI agent; key=%d", self.key)
            self._ipmi_agent.start_agent()

    @handler("InputVoltageDownEvent")
    def on_input_voltage_down(self, event, *args, **kwargs):
        if self.state.input_voltage == 0:
            logger.debug("Stopping IPMI agent; key=%d", self.key)
            self._ipmi_agent.stop_agent()


@register_asset
class PSU(StaticAsset):
    """PSU """

    channel = "engine-psu"
    StateManagerCls = in_state.PSUStateManager

    class IPMIstatus:
        """hex codes for IPMI status"""

        off = "0x08"
        on = "0x01"

    def __init__(self, asset_info):
        super(PSU, self).__init__(asset_info)

        # only ServerWithBmc needs to handle events (in order to update sensors)
        if not self._state.supports_bmc:
            self.removeHandler(self.on_asset_did_power_off)
            self.removeHandler(self.on_asset_did_power_on)
            self.removeHandler(self.update_load_sensors)

        else:
            self._sensor_repo = SensorRepository(
                str(asset_info["key"])[:-1], enable_thermal=True
            )
            self._psu_sensor_names = self._state.get_psu_sensor_names()

    def _get_psu_sensor(self, sensor_name):
        """Get the PSU's sensor based on sensor name; returns None if there is
        no BMC or the sensor is not found.
        """
        psu_sensor = None

        if (self._state.supports_bmc) and (sensor_name in self._psu_sensor_names):
            psu_sensor = self._sensor_repo.get_sensor_by_name(
                self._psu_sensor_names[sensor_name]
            )

        return psu_sensor

    def _exec_on_psu_sensor(self, sensor_name, sensor_attribute_key, *args):
        """Either execute a function or set the property of the given sensor."""
        psu_sensor = self._get_psu_sensor(sensor_name)
        return_value = None

        try:
            # Throws AttributeError when either:
            # 1) psu_sensor is None, or
            # 2) sensor_attribute_key doesn't exist on the sensor
            psu_sensor_attribute = getattr(psu_sensor, sensor_attribute_key)

            if callable(psu_sensor_attribute):
                # Spread args as arguments for function on the sensor
                return_value = psu_sensor_attribute(*args)
            else:
                # If setting the sensor's property, use the 0th argument
                setattr(psu_sensor, sensor_attribute_key, args[0])
        except AttributeError as attribute_error:
            # Not a severe error because sensors not found can be ignored
            logger.debug(
                "[%s.%s] not found; CAUSE: %s",
                sensor_name,
                sensor_attribute_key,
                str(attribute_error),
            )

        # This is not None only when the executed function returns a value
        return return_value

    def _set_psu_sensor(self, sensor_name, value):
        """Set the PSU's sensor value based on sensor name"""
        self._exec_on_psu_sensor(sensor_name, "sensor_value", value)

    def _power_on_sequence(self):
        """Execute the list of tasks when power on or when power resumes."""
        self._set_psu_sensor("psuStatus", PSU.IPMIstatus.on)
        self._exec_on_psu_sensor("psuFan", "set_to_defaults")

    def _power_off_sequence(self):
        """Execute the list of tasks when power off or when power disappears."""
        self._exec_on_psu_sensor("psuFan", "set_to_off")
        self._set_psu_sensor("psuStatus", PSU.IPMIstatus.off)

    @handler("PowerButtonOffEvent")
    def on_asset_did_power_off(self, event, *args, **kwargs):
        """PSU status was set to failed"""
        self._power_off_sequence()

    @handler("PowerButtonOnEvent")
    def on_asset_did_power_on(self, event, *args, **kwargs):
        """PSU was brought back up"""
        self._power_on_sequence()

    def _update_load_sensors(self, load):
        """Update psu sensors associated with load
        Args:
            load: amperage change
        """
        self._set_psu_sensor("psuCurrent", int(load))
        self._set_psu_sensor("psuPower", int(load) * 10)

    @handler("ChildLoadUpEvent", "ChildLoadDownEvent", priority=1)
    def update_load_sensors(self, event, *args, **kwargs):
        """Change values of BMC sensors associated with load
        """
        self._update_load_sensors(event.load.new)

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        asset_event = super().on_input_voltage_up(event, args, kwargs)
        if not asset_event.state.unchanged() and asset_event.state.new:
            self._power_on_sequence()

        return asset_event

    @handler("InputVoltageDownEvent")
    def on_input_voltage_down(self, event, *args, **kwargs):
        asset_event = super().on_input_voltage_down(event, args, kwargs)
        if not asset_event.state.unchanged() and not asset_event.state.new:
            self._power_off_sequence()

        return asset_event
