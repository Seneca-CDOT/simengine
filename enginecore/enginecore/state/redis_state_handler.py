"""RedisStateHandler handles published data in enginecore redis pub/sub channels"""
import logging
import os
import math
from queue import Queue, Empty

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher
from circuits import Component, Debugger, handler
import redis

from enginecore.state.redis_channels import RedisChannels
from enginecore.state.net.ws_server import WebSocket

logger = logging.getLogger(__name__)


class EngineStateTracker(Component):
    timeout = 3

    def __init__(self):
        super().__init__()
        self._load_done_queue = Queue()

    @handler("AllLoadBranchesDone")
    def on_load_branch_done(self, event, *args, **kwargs):
        """Handler waits for engine to complete a power iteration"""
        self._load_done_queue.put(event)

    def wait_load_queue(self):
        """Block execution until load iteration is completed"""
        try:
            return self._load_done_queue.get(timeout=EngineStateTracker.timeout)
        except Empty:
            pass


class RedisStateHandler(Component):
    """Notifies engine of redis store updates of interest"""

    def __init__(self, engine_cls, debug=False, force_snmp_init=True):
        super(RedisStateHandler, self).__init__()

        self._state_tracker = EngineStateTracker()

        logger.info("Initializing websocket server...")
        # set up a web socket server
        socket_conf = {
            "host": os.environ.get("SIMENGINE_SOCKET_HOST"),
            "port": int(os.environ.get("SIMENGINE_SOCKET_PORT")),
        }
        self._server = Server((socket_conf["host"], socket_conf["port"])).register(self)

        # Worker(process=False).register(self)
        Static().register(self._server)
        Logger().register(self._server)

        if debug:
            Debugger(events=False).register(self)
        self._ws = WebSocket().register(self._server)

        WebSocketsDispatcher("/simengine").register(self._server)

        logger.info("Initializing engine...")
        self._engine = engine_cls(force_snmp_init=force_snmp_init).register(self)
        self._engine.subscribe_tracker(self._ws)
        self._engine.subscribe_tracker(self._state_tracker)

        # Use redis pub/sub communication
        logger.info("Initializing redis connection...")
        self._redis_store = redis.StrictRedis(host="localhost", port=6379)

    # -- Handle Power Changes --
    @handler(RedisChannels.state_update_channel)
    def on_asset_power_state_change(self, data):
        """On user changing asset status"""
        self._engine.handle_state_update(
            data["key"], data["old_state"], data["new_state"]
        )
        if data["old_state"] != data["new_state"]:
            self._state_tracker.wait_load_queue()

    @handler(RedisChannels.voltage_update_channel)
    def on_voltage_state_change(self, data):
        """React to voltage drop or voltage restoration"""
        self._engine.handle_voltage_update(data["old_voltage"], data["new_voltage"])
        if not math.isclose(data["old_voltage"], data["new_voltage"]):
            self._state_tracker.wait_load_queue()

    @handler(RedisChannels.oid_update_channel)
    def on_snmp_device_oid_change(self, data):
        """React to OID getting updated through SNMP interface"""
        value = (self._redis_store.get(data)).decode()
        asset_key, oid = data.split("-")

        # snmpsimd format has crazy number of whitespaces in object id
        oid = oid.replace(" ", "")
        # value is stored as "datatype | oid-value"
        _, oid_value = value.split("|")

        self._engine.handle_oid_update(int(asset_key), oid, oid_value)

    @handler(RedisChannels.model_update_channel)
    def on_model_reload_reqeust(self, _):
        """Detect topology changes to the system architecture"""
        self._engine.reload_model()

    # -- Battery Updates --
    @handler(RedisChannels.battery_update_channel)
    def on_battery_level_change(self, data):
        """On UPS battery charge drop/increase"""
        self._engine.handle_battery_update(
            data["key"], data["old_battery"], data["new_battery"]
        )

    @handler(RedisChannels.battery_conf_charge_channel)
    def on_battery_charge_factor_up(self, data):
        """On UPS battery charge increase"""
        self._engine.assets[data["key"]].charge_speed_factor = data["factor"]

    @handler(RedisChannels.battery_conf_drain_channel)
    def on_battery_charge_factor_down(self, data):
        """On UPS battery charge increase"""
        self._engine.assets[data["key"]].drain_speed_factor = data["factor"]

    # -- Thermal Updates --
    @handler(RedisChannels.ambient_update_channel)
    def on_ambient_temperature_change(self, data):
        """Ambient updated"""
        self._engine.handle_ambient_update(data["old_ambient"], data["new_ambient"])

    @handler(RedisChannels.sensor_conf_th_channel)
    def on_new_sensor_thermal_impact(self, data):
        """Add new thermal impact (sensor to sensor)"""
        self._engine.assets[data["key"]].add_sensor_thermal_impact(
            **data["relationship"]
        )

    @handler(RedisChannels.cpu_usg_conf_th_channel)
    def on_new_cpu_thermal_impact(self, data):
        """Add new thermal impact (cpu load to sensor)"""
        self._engine.assets[data["key"]].add_cpu_thermal_impact(**data["relationship"])

    @handler(RedisChannels.str_cv_conf_th_channel)
    def on_new_cv_thermal_impact(self, data):
        """Add new thermal impact (sensor to cv)"""
        self._engine.assets[data["key"]].add_storage_cv_thermal_impact(
            **data["relationship"]
        )

    @handler(RedisChannels.str_drive_conf_th_channel)
    def on_new_hd_thermal_impact(self, data):
        """Add new thermal impact (sensor to physical drive)"""
        self._engine.assets[data["key"]].add_storage_pd_thermal_impact(
            **data["relationship"]
        )
