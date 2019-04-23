"""This file contains definitions of Assets 

Each asset class contains reactive logic associated with certain events. 

Example:
    a PDU asset will be instantiated if there's a node labeled as "PDU" in a graph db (:PDU),
    isntance of a PDU asset can react to upstream power loss or any other event defined 
    as a handler. It can also wrap SNMPAgent if supported.

"""
# **due to circuit callback signature
# pylint: disable=W0613


import os
import json
import time
import logging
import operator
from threading import Thread
from collections import namedtuple
import datetime as dt

from circuits import Component, handler
import enginecore.state.state_managers as sm
from enginecore.state.asset_definition import register_asset, SUPPORTED_ASSETS
from enginecore.state.agent import IPMIAgent, SNMPAgent, StorCLIEmulator
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.state_initializer import get_temp_workplace_dir

PowerEventResult = namedtuple(
    "PowerEventResult", "old_state new_state asset_key asset_type"
)
PowerEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)
LoadEventResult = namedtuple(
    "LoadEventResult", "load_change old_load new_load asset_key asset_type"
)
LoadEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)


class Asset(Component):
    """Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self.state.reset_boot_time()
        self.state.update_load(0)

    @property
    def key(self):
        """ Get ID assigned to the asset """
        return self.state.key

    @property
    def state(self):
        """State manager instance"""
        return self._state

    def power_up(self):
        """Power up this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            new_state=self.state.power_up(),
        )

    def shut_down(self):
        """Shut down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            new_state=self.state.shut_down(),
        )

    def power_off(self):
        """Power down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            new_state=self.state.power_off(),
        )

    def _update_load(self, load_change, arithmetic_op, msg=""):
        """React to load changes by updating asset load
        
        Args:
            load_change(float): how much AMPs need to be added/subtracted
            arithmetic_op(callable): calculates new load (receives old load & measured load change)
            msg(str): message to be printed
        
        Returns:
            LoadEventResult: Event result containing old & new load values as well as value subtracted/added
        """

        old_load = self.state.load
        new_load = arithmetic_op(old_load, load_change)

        if msg:
            logging.info(msg.format(self.state.key, old_load, load_change, new_load))

        self.state.update_load(new_load)

        return LoadEventResult(
            load_change=load_change,
            old_load=old_load,
            new_load=new_load,
            asset_key=self.state.key,
        )

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased")
    def on_load_increase(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        increased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was increased by {}, new load={};"
        return self._update_load(increased_by, lambda old, change: old + change, msg)

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        decreased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was decreased by {}, new load={};"
        return self._update_load(decreased_by, lambda old, change: old - change, msg)

    # @handler("VoltageIncreased")
    # def on_voltage_increase(self, event, *args, **kwargs):
    #     """React to voltage spikes"""

    #     if self.state.status:
    #         return

    #     min_voltage, _ = self.state.min_voltage_prop()
    #     if min_voltage and kwargs["new_value"] >= min_voltage:
    #         self.state.power_up()
    #         self.state.publish_power()

    # @handler("VoltageDecreased")
    # def on_voltage_drop(self, event, *args, **kwargs):
    #     min_voltage, power_off_timeout = self.state.min_voltage_prop()
    #     if min_voltage and kwargs["new_value"] < min_voltage and self.state.status:
    #         time.sleep(power_off_timeout)
    #         self.state.power_off()
    #         self.state.publish_power()

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS

    @classmethod
    def get_state_manager_by_key(cls, key):
        """Get a state manager specific to the asset type
        Args:
            key(int): asset key
        Returns:
            StateManager: instance of the StateManager sub-class
        """
        return sm.StateManager.get_state_manager_by_key(key, cls.get_supported_assets())


class SNMPSim:
    """Snmp simulator running snmpsim program"""

    def __init__(self, key, host, port):
        self._snmp_agent = SNMPAgent(key, host, port)

    ##### Create/kill SNMP agent when state changes
    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        self._snmp_agent.stop_agent()

    @handler("ButtonPowerUpPressed", "ParentAssetPowerUp")
    def on_asset_did_power_on(self):
        self._snmp_agent.start_agent()


@register_asset
class PDU(Asset, SNMPSim):
    """Provides reactive logic for PDU & manages snmp simulator instance
    Example:
        powers down when upstream power becomes unavailable 
        powers back up when upstream power is restored
    """

    channel = "engine-pdu"
    StateManagerCls = sm.PDUStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, PDU.StateManagerCls(asset_info))
        # Run snmpsim instance
        SNMPSim.__init__(
            self,
            key=asset_info["key"],
            host=asset_info["host"] if "host" in asset_info else "localhost",
            port=asset_info["port"] if "port" in asset_info else 161,
        )

        self.state.update_agent(self._snmp_agent.pid)

        agent_info = self.state.agent
        if not agent_info[1]:
            logging.error(
                "Asset:[%s] - agent process (%s) failed to start!",
                self.state.key,
                agent_info[0],
            )
        else:
            logging.info(
                "Asset:[%s] - agent process (%s) is up & running",
                self.state.key,
                agent_info[0],
            )

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Power off & stop snmp simulator instance when parent is down"""

        e_result = self.power_off()

        if e_result.new_state == e_result.old_state:
            event.success = False
        else:
            self._snmp_agent.stop_agent()

        return e_result

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """Power up PDU when upstream power source is restored """
        e_result = self.power_up()
        event.success = e_result.new_state != e_result.old_state

        return e_result


@register_asset
class UPS(Asset, SNMPSim):
    """Provides reactive logic for UPS & manages snmp simulator instance

    Example:
        drains battery when upstream power becomes unavailable 
        charges battery when upstream power is restored
    """

    channel = "engine-ups"
    StateManagerCls = sm.UPSStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, UPS.StateManagerCls(asset_info))
        SNMPSim.__init__(
            self,
            key=asset_info["key"],
            host=asset_info["host"] if "host" in asset_info else "localhost",
            port=asset_info["port"] if "port" in asset_info else 161,
        )

        self.state.update_agent(self._snmp_agent.pid)

        # Store known { wattage: time_remaining } key/value pairs (runtime graph)
        self._runtime_details = json.loads(asset_info["runtime"])

        # Track upstream power availability
        self._parent_up = True
        self._charge_speed_factor = 1
        self._drain_speed_factor = 1

        # Threads responsible for battery charge/discharge
        self._battery_drain_t = None
        self._battery_charge_t = None

        self._start_time_battery = None

        # set battery level to max
        self.state.update_battery(self.state.battery_max_level)

        # get charge per second using full recharge time (hrs)
        self._charge_per_second = self.state.battery_max_level / (
            self.state.full_recharge_time * 60 * 60
        )

        # set temp on start
        self._state.update_temperature(7)

        agent_info = self.state.agent
        if not agent_info[1]:
            logging.error(
                "Asset:[%s] - agent process (%s) failed to start!",
                self.state.key,
                agent_info[0],
            )
        else:
            logging.info(
                "Asset:[%s] - agent process (%s) is up & running",
                self.state.key,
                agent_info[0],
            )

    def _cacl_time_left(self, wattage):
        """Approximate runtime estimation based on current battery level"""
        return (
            self._calc_full_power_time_left(wattage) * self.state.battery_level
        ) / self.state.battery_max_level

    def _calc_full_power_time_left(self, wattage):
        """Approximate runtime estimation for the fully-charged battery"""
        close_wattage = min(self._runtime_details, key=lambda x: abs(int(x) - wattage))
        close_timeleft = self._runtime_details[close_wattage]
        return (close_timeleft * int(close_wattage)) / wattage  # inverse proportion

    def _calc_battery_discharge(self):
        """Approximate battery discharge per second based on the runtime model & current wattage draw

        Returns:
            float: discharge per second 
        """
        # return 100
        wattage = self.state.wattage
        fp_estimated_timeleft = self._calc_full_power_time_left(wattage)
        return self.state.battery_max_level / (fp_estimated_timeleft * 60)

    def _drain_battery(self, parent_up):
        """When parent is not available -> drain battery 
        
        Args:
            parent_up(callable): indicates if the upstream power is available
        """

        battery_level = self.state.battery_level
        blackout = False

        # keep draining battery while its level remains above 0, UPS is on and parent is down
        while battery_level > 0 and self.state.status and not parent_up():

            # calculate new battery level
            battery_level = battery_level - (
                self._calc_battery_discharge() * self._drain_speed_factor
            )
            seconds_on_battery = (dt.datetime.now() - self._start_time_battery).seconds

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )
            self.state.update_time_on_battery(seconds_on_battery * 100)

            if seconds_on_battery > 5 and not blackout:
                blackout = True
                self.state.update_transfer_reason(
                    sm.UPSStateManager.InputLineFailCause.blackout
                )

            time.sleep(1)

        # kill the thing if still breathing
        if self.state.status and not parent_up():
            self._snmp_agent.stop_agent()
            self.state.power_off()
            self.state.publish_power()

    def _charge_battery(self, parent_up, power_up_on_charge=False):
        """Charge battery when there's upstream power source & battery is not full
                
        Args:
            parent_up(callable): indicates if the upstream power is available
            power_up_on_charge(boolean): indicates if the asset should be powered up when min charge level is achieved

        """

        battery_level = self.state.battery_level
        powered = False

        # keep charging battery while its level is less than max & parent is up
        while battery_level < self.state.battery_max_level and parent_up():

            # calculate new battery level
            battery_level = battery_level + (
                self._charge_per_second * self._charge_speed_factor
            )

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )

            # power up on min charge level
            if (not powered and power_up_on_charge) and (
                battery_level > self.state.min_restore_charge_level
            ):
                e_result = self.power_up()
                powered = e_result.new_state
                self.state.publish_power()

            time.sleep(1)

    def _launch_battery_drain(self):
        """Start a thread that will decrease battery level """

        self._start_time_battery = dt.datetime.now()

        # update state details
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onBattery)
        self.state.update_transfer_reason(
            sm.UPSStateManager.InputLineFailCause.deepMomentarySag
        )

        # launch a thread
        self._battery_drain_t = Thread(
            target=self._drain_battery,
            args=(lambda: self._parent_up,),
            name="battery_drain:{}".format(self.key),
        )
        self._battery_drain_t.daemon = True
        self._battery_drain_t.start()

    def _launch_battery_charge(self, power_up_on_charge=False):
        """Start a thread that will charge battery level """
        self.state.update_time_on_battery(0)

        # update state details
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onLine)
        self.state.update_transfer_reason(
            sm.UPSStateManager.InputLineFailCause.noTransfer
        )

        # launch a thread
        self._battery_charge_t = Thread(
            target=self._charge_battery,
            args=(lambda: self._parent_up, power_up_on_charge),
            name="battery_charge:{}".format(self.key),
        )
        self._battery_charge_t.daemon = True
        self._battery_charge_t.start()

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Upstream power was lost"""

        self._parent_up = False

        # If battery is still alive -> keep UPS up
        if self.state.battery_level:
            self._launch_battery_drain()
            event.success = False
            return

        # Battery is dead
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.off)

        e_result = self.power_off()
        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("SignalDown")
    def on_signal_down_received(self, event, *args, **kwargs):
        """UPS can be powered down by snmp command"""
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.off)

        if "graceful" in kwargs and kwargs["graceful"]:
            e_result = self.shut_down()
        else:
            e_result = self.power_off()

        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("ButtonPowerUpPressed")
    def on_ups_signal_up(self):
        if self._parent_up:
            self._launch_battery_charge()
        else:
            self._launch_battery_drain()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):

        self._parent_up = True
        battery_level = self.state.battery_level
        self._launch_battery_charge(power_up_on_charge=(not battery_level))

        if battery_level:
            e_result = self.power_up()
            event.success = e_result.new_state != e_result.old_state

            return e_result

        event.success = False
        return None

    @handler("AmbientDecreased", "AmbientIncreased")
    def on_ambient_updated(self, event, *args, **kwargs):
        self._state.update_temperature(7)

    @property
    def charge_speed_factor(self):
        """Estimated charge/sec will be multiplied by this value"""
        return self._charge_speed_factor

    @charge_speed_factor.setter
    def charge_speed_factor(self, speed):
        self._charge_speed_factor = speed

    @property
    def drain_speed_factor(self):
        """Estimated drain/sec will be multiplied by this value"""
        return self._drain_speed_factor

    @drain_speed_factor.setter
    def drain_speed_factor(self, speed):
        self._drain_speed_factor = speed

    def _update_load(self, load_change, arithmetic_op, msg=""):
        upd_result = super()._update_load(load_change, arithmetic_op, msg)
        # re-calculate time left based on updated load
        self.state.update_time_left(self._cacl_time_left(self.state.wattage) * 60 * 100)
        return upd_result


@register_asset
class Outlet(Asset):

    channel = "engine-outlet"
    StateManagerCls = sm.OutletStateManager

    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))

    ##### React to any events of the connected components #####

    @handler("SignalDown", priority=1)
    def on_signal_down_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state 
        (if if one is updated, other ones should be updated as well)"""
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOff)

    @handler("SignalUp", priority=1)
    def on_signal_up_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state"""
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOn)

    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        """ React to events with power down """
        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_off_delay())

        return self.power_off()

    @handler("ParentAssetPowerUp", "SignalUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """ React to events with power up """

        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_on_delay())

        e_result = self.power_up()
        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("SignalReboot")
    def on_reboot_request_received(self, event, *args, **kwargs):
        """Received reboot request"""
        old_state = self.state.status

        self.power_off()
        e_result_up = self.power_up()
        if not e_result_up.new_state:
            event.success = False

        return PowerEventResult(
            old_state=old_state,
            new_state=e_result_up.new_state,
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
        )


@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = sm.StaticDeviceStateManager

    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))
        self.state.update_load(self.state.power_usage)

    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        return self.power_off()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        return self.power_up()


@register_asset
class Lamp(StaticAsset):
    """A simple demonstration type """

    channel = "engine-lamp"


@register_asset
class Server(StaticAsset):
    """Asset controlling a VM (without IPMI support) """

    channel = "engine-server"
    StateManagerCls = sm.ServerStateManager

    def __init__(self, asset_info):
        super(Server, self).__init__(asset_info)
        self.state.power_up()


@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI support """

    channel = "engine-bmc"
    StateManagerCls = sm.BMCServerStateManager

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

        agent_info = self.state.agent
        log_msg = "is up & running" if agent_info[1] else "failed to start!"
        logging.info(
            "Asset:[%s] - agent process (%s) %s", self.state.key, agent_info[0], log_msg
        )
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

    def add_storage_cv_thermal_impact(self, source, controller, cv, event):
        """Add new sensor & cachevault thermal relationship
        Args:
            source(str): name of the source sensor causing thermal changes
            cv(str): serial number of the cachevault
        """
        sensor = self._sensor_repo.get_sensor_by_name(source)
        sensor.add_cv_thermal_impact(controller, cv, event)

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

    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        self._ipmi_agent.stop_agent()
        e_result = self.power_off()
        if e_result.old_state != e_result.new_state:
            self._sensor_repo.shut_down_sensors()
        return e_result

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        self._ipmi_agent.start_agent()
        e_result = self.power_up()
        if e_result.old_state != e_result.new_state:
            self._sensor_repo.power_up_sensors()
        return e_result

    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        self._sensor_repo.shut_down_sensors()

    @handler("ButtonPowerUpPressed")
    def on_asset_did_power_on(self):
        self._sensor_repo.power_up_sensors()


@register_asset
class PSU(StaticAsset):
    """PSU """

    channel = "engine-psu"
    StateManagerCls = sm.PSUStateManager

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
