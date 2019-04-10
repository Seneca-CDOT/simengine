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

    def __init__(self):
        pass

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
    @record
    @Randomizer.randomize_method((lambda _: random.randrange(18, 35),))
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
        cls.get_store().set("mains-source", "0")
        cls.get_store().publish(RedisChannels.mains_update_channel, "0")

    @classmethod
    @record
    @Randomizer.randomize_method()
    def power_restore(cls):
        """Simulate complete power restoration"""
        cls.get_store().set("mains-source", "1")
        cls.get_store().publish(RedisChannels.mains_update_channel, "1")

    @classmethod
    def mains_status(cls):
        """Get wall power status"""
        return int(cls.get_store().get("mains-source").decode())

    @classmethod
    def get_ambient_props(cls):
        """Get runtime ambient properties (ambient behaviour description)"""
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            props = GraphReference.get_ambient_props(session)
            return props

    @classmethod
    def set_ambient_props(cls, props):
        """Update runtime thermal properties of the room temperature"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.set_ambient_props(session, props)
