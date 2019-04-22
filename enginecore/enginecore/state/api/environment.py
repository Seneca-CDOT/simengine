"""Tools for managing virtual system environment"""
import random
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
        cls.get_store().publish(RedisChannels.model_update_channel, "reload")

    @classmethod
    def get_ambient(cls):
        """Retrieve current ambient value"""
        temp = cls.get_store().get("ambient")
        return int(temp.decode()) if temp else 0

    @classmethod
    def get_voltage(cls):
        """Get Wall-power voltage"""
        voltage = cls.get_store().get("voltage")
        return float(voltage.decode()) if voltage else 120.0

    @classmethod
    def set_voltage(cls, value):
        """Update voltage"""
        old_voltage = cls.get_voltage()
        cls.get_store().set("voltage", str(float(value)))
        cls.get_store().publish(
            RedisChannels.voltage_update_channel, "{}-{}".format(old_voltage, value)
        )

    @classmethod
    def get_min_voltage(cls):
        """Minimum voltage required for assets to function;
        dropping below this point will result in assets getting powered down
        Returns:
            float: minimum voltage (in Volts)
        """
        return 90.0

    @classmethod
    def power_source_available(cls):
        """Check if the mains is present and voltage is above minimum
        Returns:
            bool: true if assets can be powered up by the wall
        """
        return cls.get_voltage() >= cls.get_min_voltage()

    @classmethod
    @record
    @Randomizer.randomize_method(
        (lambda self: random.randrange(*self.get_ambient_props()[1].values()),)
    )
    def set_ambient(cls, value):
        """Update ambient value"""
        old_temp = cls.get_ambient()
        cls.get_store().set("ambient", str(int(value)))
        cls.get_store().publish(
            RedisChannels.ambient_update_channel, "{}-{}".format(old_temp, value)
        )

    @classmethod
    @record
    @Randomizer.randomize_method()
    def power_outage(cls):
        """Simulate complete power outage/restoration"""
        cls.set_voltage(0.0)
        cls.get_store().publish(RedisChannels.mains_update_channel, "0")

    @classmethod
    @record
    @Randomizer.randomize_method()
    def power_restore(cls):
        """Simulate complete power restoration"""
        cls.set_voltage(120.0)
        cls.get_store().publish(RedisChannels.mains_update_channel, "1")

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
        """Update runtime thermal properties of the room temperature"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.set_ambient_props(session, props)
