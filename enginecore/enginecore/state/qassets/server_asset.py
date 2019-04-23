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
from threading import Thread

from circuits import handler

from enginecore.state.qassets.static_asset import StaticAsset
from enginecore.state.qassets.asset_definition import register_asset
import enginecore.state.qassets.state_managers as sm

from enginecore.state.agent import IPMIAgent, StorCLIEmulator
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.state_initializer import get_temp_workplace_dir


@register_asset
class Server(StaticAsset):
    """Asset controlling a VM (without IPMI support)"""

    channel = "engine-server"
    StateManagerCls = sm.ServerStateManager

    def __init__(self, asset_info):
        super(Server, self).__init__(asset_info)
        self.state.power_up()


@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI and StorCLI support"""

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
