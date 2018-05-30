from circuits import Component, handler
import redis

SUPPORTED_ASSETS = {}

def register_asset(cls):
    """
    This decorator maps string class names to classes
    (It is basically a factory)
    """
    SUPPORTED_ASSETS[cls.__name__.lower()] = cls

class Asset(Component):
    def __init__(self, key):
        super(Asset, self).__init__()
        self._key = key
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
    
    def get_key(self):
        return self._key

@register_asset
class PDU(Asset):
    channel = "pdu"
    
    @handler("OutletPowerDown")
    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-pdu', '0')

    @handler("OutletPowerUp")
    def power_up(self):
        print("Powering up {}".format(self._key))
        self.redis_store.set(str(self._key) + '-pdu', '1')

@register_asset
class Outlet(Asset):
    channel = "outlet"
    
    @handler("PDUPowerDown")
    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-outlet', '0')

    @handler("PDUPowerUp")
    def power_up(self):
        print("Powering up {}".format(self._key))
        # TODO: check if OID for this socket is on
        self.redis_store.set(str(self._key) + '-outlet', '1')


