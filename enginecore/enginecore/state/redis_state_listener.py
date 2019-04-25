"""StateListener monitors any updates to assets/OIDs 
& determines if the event affects other (connected) assets

The daemon initializes a WebSocket & Redis event listener component
and reacts to state updates by dispatching circuits events that are, in turn,
handled by individual assets.

"""
import json
import logging

from circuits import Component, Event, Timer, handler  # , task
import redis

from enginecore.state.redis_channels import RedisChannels


class Engine(Component):
    channel = "engine"

    @handler(RedisChannels.state_update_channel)
    def handle_state_update(self, data):
        print("Handling state updates")
        print(data)


class StateListener(Component):
    """Top-level component that instantiates assets 
    & maps redis events to circuit events
    """

    def __init__(self, debug=False, force_snmp_init=False):
        super(StateListener, self).__init__()
        # Use redis pub/sub communication
        logging.info("Initializing redis connection...")

        self._redis_store = redis.StrictRedis(host="localhost", port=6379)

        # set up a web socket server
        # socket_conf = {
        #     "host": os.environ.get("SIMENGINE_SOCKET_HOST"),
        #     "port": int(os.environ.get("SIMENGINE_SOCKET_PORT")),
        # }

        self._bat_pubsub = self._redis_store.pubsub()
        self._state_pubsub = self._redis_store.pubsub()
        self._thermal_pubsub = self._redis_store.pubsub()

        self._engine = Engine().register(self)
        self._subscribe_to_channels()

    def _subscribe_to_channels(self):
        """Subscribe to redis channels"""

        logging.info("Initializing redis subscriptions...")

        # State Channels
        self._state_pubsub.psubscribe(
            RedisChannels.oid_update_channel,  # snmp oid updates
            RedisChannels.state_update_channel,  # power state changes
            RedisChannels.mains_update_channel,  # wall power updates
            RedisChannels.model_update_channel,  # model changes
            RedisChannels.voltage_update_channel,  # wallpower voltage changes
        )

        # Battery Channel
        self._bat_pubsub.psubscribe(
            RedisChannels.battery_update_channel,  # battery level updates
            RedisChannels.battery_conf_drain_channel,  # update drain speed (factor)
            RedisChannels.battery_conf_charge_channel,  # update charge speed (factor)
        )

        # Thermal Channels
        self._thermal_pubsub.psubscribe(
            RedisChannels.ambient_update_channel,  # on ambient changes
            RedisChannels.sensor_conf_th_channel,  # new sensor->sensor relationship
            RedisChannels.cpu_usg_conf_th_channel,  # new cpu_usage->sensor relationship
            # new sensor->cache_vault relationship
            RedisChannels.str_cv_conf_th_channel,
            # new sensor->phys_drive relationship
            RedisChannels.str_drive_conf_th_channel,
        )

    def monitor_battery(self):
        """Monitor battery in a separate pub/sub stream"""
        message = self._bat_pubsub.get_message()

        # validate message
        if (
            (not message)
            or ("data" not in message)
            or (not isinstance(message["data"], bytes))
        ):
            return

        data = message["data"].decode("utf-8")
        channel = message["channel"].decode()

        try:
            logging.info(
                "[REDIS:BATTERY] Received a message in channel [%s]: %s", channel, data
            )

            if channel == RedisChannels.battery_update_channel:
                asset_key, _ = data.split("-")
                # self._notify_client(
                #     ServerToClientRequests.asset_upd,
                #     {
                #         "key": int(asset_key),
                #         "battery": self._assets[int(asset_key)].state.battery_level,
                #     },
                # )

            elif channel == RedisChannels.battery_conf_charge_channel:
                asset_key, _ = data.split("-")
                _, speed = data.split("|")
                # self._assets[int(asset_key)].charge_speed_factor = float(speed)
            elif channel == RedisChannels.battery_conf_drain_channel:
                asset_key, _ = data.split("-")
                _, speed = data.split("|")
                # self._assets[int(asset_key)].drain_speed_factor = float(speed)

        # TODO: this error is ttoo generic (doesn't apply to all the monitoring functions)
        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)

    def _get_message_info(self, message):

        # validate message
        # if (
        #     (not message)
        #     or ("data" not in message)
        #     or (not isinstance(message["data"], bytes))
        # ):
        #     return

        data = message["data"].decode("utf-8")
        channel = message["channel"].decode()

    def monitor_state(self):
        """ listens to redis events """

        message = self._state_pubsub.get_message()

        # validate message
        if (
            (not message)
            or ("data" not in message)
            or (not isinstance(message["data"], bytes))
        ):
            return

        data = message["data"].decode("utf-8")

        # interpret the published message
        # "state-upd" indicates that certain asset was powered on/off by the interface(s)
        # "oid-upd" is published when SNMPsim updates an OID
        channel = message["channel"].decode()

        try:

            logging.info(
                "[REDIS:POWER] Received a message in channel [%s]: %s", channel, data
            )

            self.fire(Event.create(channel, {}), self._engine)

            if channel == RedisChannels.state_update_channel:
                asset_key, asset_status = data.split("-")
                # if asset_type in Asset.get_supported_assets():
                # self._handle_state_update(int(asset_key), asset_status)
            elif channel == RedisChannels.voltage_update_channel:
                old_voltage, new_voltage = map(float, data.split("-"))
                logging.info(
                    'System voltage change from "%s" to "%s"', old_voltage, new_voltage
                )

                # react to voltage drop or voltage restoration
                # if new_voltage == 0.0:
                # self._handle_wallpower_update(power_up=False)
                # elif old_voltage < ISystemEnvironment.get_min_voltage() <= new_voltage:
                # self._handle_wallpower_update(power_up=True)

                # event = PowerEventMap.map_voltage_event(old_voltage, new_voltage)
                # list(map(lambda asset: self.fire(event, asset), self._assets.values()))

            elif channel == RedisChannels.mains_update_channel:
                new_state = int(data)

                # self._notify_client(
                #     ServerToClientRequests.mains_upd, {"mains": new_state}
                # )

                # self.fire(PowerEventMap.map_mains_event(data), self._sys_environ)

            elif channel == RedisChannels.oid_update_channel:
                value = (self._redis_store.get(data)).decode()
                asset_key, oid = data.split("-")
                # self._handle_oid_update(int(asset_key), oid, value)

            elif channel == RedisChannels.model_update_channel:
                self._state_pubsub.unsubscribe()
                self._bat_pubsub.unsubscribe()

                # self._reload_model()
                self._subscribe_to_channels()

        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)

    def monitor_thermal(self):
        """Monitor thermal updates in a separate pub/sub channel"""

        message = self._thermal_pubsub.get_message()

        # validate message
        if (
            (not message)
            or ("data" not in message)
            or (not isinstance(message["data"], bytes))
        ):
            return

        data = message["data"].decode("utf-8")
        channel = message["channel"].decode()

        try:
            logging.info(
                "[REDIS:THERMAL] Received a message in channel [%s]: %s", channel, data
            )

            if channel == RedisChannels.ambient_update_channel:
                old_temp, new_temp = map(float, data.split("-"))
                # self._handle_ambient_update(new_temp=float(new_temp), old_temp=old_temp)
            elif channel == RedisChannels.sensor_conf_th_channel:
                new_rel = json.loads(data)
                # self._assets[new_rel["key"]].add_sensor_thermal_impact(
                #     **new_rel["relationship"]
                # )
            elif channel == RedisChannels.cpu_usg_conf_th_channel:
                new_rel = json.loads(data)
                # self._assets[new_rel["key"]].add_cpu_thermal_impact(
                #     **new_rel["relationship"]
                # )
            elif channel == RedisChannels.str_cv_conf_th_channel:
                new_rel = json.loads(data)
                # self._assets[new_rel["key"]].add_storage_cv_thermal_impact(
                #     **new_rel["relationship"]
                # )
            elif channel == RedisChannels.str_drive_conf_th_channel:
                new_rel = json.loads(data)
                # self._assets[new_rel["key"]].add_storage_pd_thermal_impact(
                #     **new_rel["relationship"]
                # )

        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)

    def started(self, *args):
        """
            Called on start
        """
        logging.info("Initializing pub/sub event handlers...")
        Timer(0.5, Event.create("monitor_state"), persist=True).register(self)
        # Timer(0.5, Event.create("monitor_battery"), persist=True).register(self)
        # Timer(0.5, Event.create("monitor_thermal"), persist=True).register(self)


if __name__ == "__main__":
    StateListener().run()
