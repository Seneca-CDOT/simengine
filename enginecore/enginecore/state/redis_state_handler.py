import logging
from circuits import Component, Event, Worker, Debugger, handler  # , task
import redis

from enginecore.state.redis_channels import RedisChannels
from enginecore.state.net.ws_requests import ServerToClientRequests
from enginecore.state.engine import Engine
from enginecore.state.event_map import PowerEventMap


class RedisStateHandler(Engine):
    """Top-level component that instantiates assets 
    & maps redis events to circuit events"""

    def __init__(self, debug=False, force_snmp_init=True):
        super(RedisStateHandler, self).__init__(debug, force_snmp_init)

        # Use redis pub/sub communication
        logging.info("Initializing redis connection...")
        self._redis_store = redis.StrictRedis(host="localhost", port=6379)

    # -- Handle Power Changes --
    @handler(RedisChannels.state_update_channel)
    def on_asset_power_state_change(self, data):
        """On user changing asset status"""
        self.handle_state_update(data["key"], data["status"])

    @handler(RedisChannels.voltage_update_channel)
    def on_voltage_state_change(self, data):
        """React to voltage drop or voltage restoration"""
        self.handle_voltage_update(data["old_voltage"], data["new_voltage"])

    @handler(RedisChannels.mains_update_channel)
    def on_wallpower_state_change(self, data):
        """On balckouts/power restorations"""
        self._notify_client(ServerToClientRequests.mains_upd, {"mains": data["status"]})
        self.fire(PowerEventMap.map_mains_event(data["status"]), self._sys_environ)

    @handler(RedisChannels.oid_update_channel)
    def on_snmp_device_oid_change(self, data):
        """React to OID getting updated through SNMP interface"""
        value = (self._redis_store.get(data)).decode()
        asset_key, oid = data.split("-")
        self.handle_oid_update(int(asset_key), oid, value)

    @handler(RedisChannels.model_update_channel)
    def on_model_reload_reqeust(self, _):
        """Detect topology changes to the system architecture"""
        self._reload_model()

    # -- Battery Updates --
    @handler(RedisChannels.battery_update_channel)
    def on_battery_level_change(self, data):
        """On UPS battery charge drop/increase"""
        self._notify_client(
            ServerToClientRequests.asset_upd,
            {
                "key": data["key"],
                "battery": self._assets[data["key"]].state.battery_level,
            },
        )

    @handler(RedisChannels.battery_conf_charge_channel)
    def on_battery_charge_factor_up(self, data):
        """On UPS battery charge increase"""
        self._assets[data["key"]].charge_speed_factor = data["factor"]

    @handler(RedisChannels.battery_conf_drain_channel)
    def on_battery_charge_factor_down(self, data):
        """On UPS battery charge increase"""
        self._assets[data["key"]].drain_speed_factor = data["factor"]

    # -- Thermal Updates --
    @handler(RedisChannels.ambient_update_channel)
    def on_ambient_temperature_change(self, data):
        """Ambient updated"""
        self.handle_ambient_update(data["old_ambient"], data["new_ambient"])

    @handler(RedisChannels.sensor_conf_th_channel)
    def on_new_sensor_thermal_impact(self, data):
        """Add new thermal impact (sensor to sensor)"""
        self._assets[data["key"]].add_sensor_thermal_impact(**data["relationship"])

    @handler(RedisChannels.cpu_usg_conf_th_channel)
    def on_new_cpu_thermal_impact(self, data):
        """Add new thermal impact (cpu load to sensor)"""
        self._assets[data["key"]].add_cpu_thermal_impact(**data["relationship"])

    @handler(RedisChannels.str_cv_conf_th_channel)
    def on_new_cv_thermal_impact(self, data):
        """Add new thermal impact (sensor to cv)"""
        self._assets[data["key"]].add_storage_cv_thermal_impact(**data["relationship"])

    @handler(RedisChannels.str_drive_conf_th_channel)
    def on_new_hd_thermal_impact(self, data):
        """Add new thermal impact (sensor to physical drive)"""
        self._assets[data["key"]].add_storage_pd_thermal_impact(**data["relationship"])
