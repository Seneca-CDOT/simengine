"""StateListener subscribes to redis channels and passes published data
to the Engine for further processing;
"""
import json
import logging
import os

from circuits import Component, Event, Timer
import redis

from enginecore.state.redis_channels import RedisChannels
from enginecore.state.engine import Engine
from enginecore.state.state_initializer import configure_env


class StateListener(Component):
    """Top-level component that instantiates assets 
    & maps redis events to circuit events
    """

    def __init__(self, debug=False, force_snmp_init=False):
        super(StateListener, self).__init__()

        # env space configuration
        configure_env(relative=debug)

        # Use redis pub/sub communication
        logging.info("Initializing redis connection...")

        redis_conf = {
            "host": os.environ.get("SIMENGINE_REDIS_HOST"),
            "port": int(os.environ.get("SIMENGINE_REDIS_PORT")),
        }
        self._redis_store = redis.StrictRedis(**redis_conf)

        self._pubsub_streams = {}
        for stream_name in ["power", "thermal", "battery", "snmp"]:
            self._pubsub_streams[stream_name] = self._redis_store.pubsub()

        self._subscribe_to_channels()
        self._engine = Engine(debug, force_snmp_init).register(self)

    def _subscribe_to_channels(self):
        """Subscribe to redis channels"""

        logging.info("Initializing redis subscriptions...")

        # State Channels
        self._pubsub_streams["power"].psubscribe(
            RedisChannels.state_update_channel,  # power state changes
            RedisChannels.mains_update_channel,  # wall power updates
            RedisChannels.model_update_channel,  # model changes
            RedisChannels.voltage_update_channel,  # wallpower voltage changes
        )

        # Thermal Channels
        self._pubsub_streams["thermal"].psubscribe(
            RedisChannels.ambient_update_channel,  # on ambient changes
            RedisChannels.sensor_conf_th_channel,  # new sensor->sensor relationship
            RedisChannels.cpu_usg_conf_th_channel,  # new cpu_usage->sensor relationship
            # new sensor->cache_vault relationship
            RedisChannels.str_cv_conf_th_channel,
            # new sensor->phys_drive relationship
            RedisChannels.str_drive_conf_th_channel,
        )

        # Battery Channel
        self._pubsub_streams["battery"].psubscribe(
            RedisChannels.battery_update_channel,  # battery level updates
            RedisChannels.battery_conf_drain_channel,  # update drain speed (factor)
            RedisChannels.battery_conf_charge_channel,  # update charge speed (factor)
        )

        # SNMPsimd channel
        self._pubsub_streams["snmp"].psubscribe(
            RedisChannels.oid_update_channel  # snmp oid updates
        )

    def monitor_redis(self, pubsub_group, json_format=True):
        """Monitors redis pubsub channels for new messages & dispatches
        corresponding events to the Engine
        Args:
            pubsub_group (redis.client.PubSub): group of pubsub channels to be monitored
        """

        message = pubsub_group.get_message()
        # validate message
        if (
            (not message)
            or ("data" not in message)
            or (not isinstance(message["data"], bytes))
        ):
            return

        data = message["data"].decode("utf-8")
        channel = message["channel"].decode()

        logging.info("Received new message in channel [%s]:", channel)
        logging.info(" > %s", data)

        self.fire(
            Event.create(channel, json.loads(data) if json_format else data),
            self._engine,
        )

    def started(self, _):
        """
            Called on start: initialize redis subscriptions
        """

        logging.info("Initializing pub/sub event handlers...")

        # timers will be monitoring new published messages every .5 seconds
        for stream_name in ["power", "thermal", "battery"]:
            stream = self._pubsub_streams[stream_name]
            Timer(
                0.5, Event.create("monitor_redis", pubsub_group=stream), persist=True
            ).register(self)

        # configure snmp channel:
        snmp_event = Event.create(
            "monitor_redis", self._pubsub_streams["snmp"], json_format=False
        )
        Timer(0.5, snmp_event, persist=True).register(self)


if __name__ == "__main__":
    StateListener().run()
