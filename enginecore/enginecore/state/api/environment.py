"""Tools for managing virtual system environment"""
import random
import math
import json

import redis

from enginecore.model.graph_reference import GraphReference
from enginecore.state.redis_channels import RedisChannels

from enginecore.tools.recorder import RECORDER as record
from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class ISystemEnvironment:
    """Exposes core physical environment properties such as ambient, wallpower"""

    redis_store = None

    def __init__(self, key=0):
        self._key = key

    @property
    def key(self):
        """ID of the system environment"""
        return self._key

    @classmethod
    def get_store(cls):
        """Get redis db handler """
        if not cls.redis_store:
            cls.redis_store = redis.StrictRedis(host="localhost", port=6379)

        return cls.redis_store

    @classmethod
    def reload_model(cls):
        """Request daemon reloading"""
        cls.get_store().publish(RedisChannels.model_update_channel, json.dumps({}))

    @classmethod
    def get_ambient(cls):
        """Retrieve current ambient value"""
        temp = cls.get_store().get("ambient")
        return int(temp.decode()) if temp else 0

    @classmethod
    def get_voltage(cls):
        """Get Wall-power voltage"""
        voltage = cls.get_store().get("voltage")
        return float(voltage.decode()) if voltage else cls.wallpower_volt_standard()

    @classmethod
    def power_source_available(cls):
        """Check if the mains is present and voltage is above minimum
        Returns:
            bool: true if assets can be powered up by the wall
        """
        return not math.isclose(cls.get_voltage(), 0.0)

    @staticmethod
    def sys_env_rand(sys_env_props):
        """Get random value based on sys environment property (voltage, ambient)"""
        return random.randrange(sys_env_props["start"], sys_env_props["end"])

    @classmethod
    @record
    @Randomizer.randomize_method(
        (lambda self: self.sys_env_rand(self.get_ambient_props()),)
    )
    def set_ambient(cls, value):
        """Update ambient value"""
        old_temp = cls.get_ambient()
        cls.get_store().set("ambient", str(int(value)))
        cls.get_store().publish(
            RedisChannels.ambient_update_channel,
            json.dumps({"old_ambient": old_temp, "new_ambient": value}),
        )

    @classmethod
    @record
    @Randomizer.randomize_method(
        (lambda self: self.sys_env_rand(self.get_voltage_props()),)
    )
    def set_voltage(cls, value):
        """Update voltage"""
        old_voltage = cls.get_voltage()
        cls.get_store().set("voltage", str(float(value)))

        if math.isclose(old_voltage, 0.0) and value > old_voltage:
            cls.get_store().publish(
                RedisChannels.mains_update_channel, json.dumps({"status": 1})
            )
        elif math.isclose(value, 0.0):
            cls.get_store().publish(
                RedisChannels.mains_update_channel, json.dumps({"status": 0})
            )

        cls.get_store().publish(
            RedisChannels.voltage_update_channel,
            json.dumps({"old_voltage": old_voltage, "new_voltage": value}),
        )

    @classmethod
    @Randomizer.randomize_method()
    def power_outage(cls):
        """Simulate complete power outage/restoration"""
        cls.set_voltage(0.0)

    @classmethod
    @Randomizer.randomize_method()
    def power_restore(cls):
        """Simulate complete power restoration"""
        cls.set_voltage(cls.wallpower_volt_standard())

    @classmethod
    def mains_status(cls):
        """Get wall power status"""
        return int(bool(cls.get_voltage()))

    @classmethod
    def get_ambient_props(cls) -> tuple:
        """Get runtime ambient properties (ambient behaviour description)
        Returns:
            thermal parameters for up/down events, randomizer ambient properties
            returns None if System Environment hasn't been initialized yet
        """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            return GraphReference.get_ambient_props(session)

    @classmethod
    def set_ambient_props(cls, props):
        """Update runtime thermal properties of the room temperature
        Args:
            props: ambient behaviour specs such as "event" (upon what event: up/down),
                   "degrees" (how much rises/dropw), "rate" (seconds),
                   "pause_at" (should stop at this temperature)
        """

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.set_ambient_props(session, props)

    @classmethod
    def get_voltage_props(cls) -> dict:
        """Get runtime voltage properties (ambient behaviour description)
        Returns:
            voltage fluctuation properties such as method being used (normal/gauss) 
            & properties associated with the random method
        """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            return GraphReference.get_voltage_props(session)

    @classmethod
    def set_voltage_props(cls, props):
        """Update runtime voltage properties of the mains power voltage"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.set_voltage_props(session, props)

    @staticmethod
    def voltage_random_methods():
        """Supported voltage fluctuation random methods"""
        return ["uniform", "gauss"]

    @staticmethod
    def wallpower_volt_standard():
        """Nominal wallpower voltage
        (120 volt system in North America)
        """
        return 120.0
