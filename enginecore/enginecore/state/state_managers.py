""" This file contains definitions of Asset classes """

from circuits import Component
import redis
from enginecore.state.graph_reference import GraphReference

class StateManger():


    def __init__(self, key):
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self._graph_db = GraphReference().get_session()
        self._key = key


    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()


    def power_down(self):
        raise NotImplementedError


    def power_up(self):
        raise NotImplementedError


class PDUStateManager(StateManger):
    

    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-pdu', '0')
    

    def power_up(self):
        print("Powering up {}".format(self._key))
        
        # parent_keys = GraphReference.get_parent_keys(self._graph_db, self._key)
        # print(parent_keys)
        self.redis_store.set(str(self._key) + '-pdu', '1')


class OutletStateManager(StateManger):


    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-outlet', '0')


    def power_up(self):
        print("Powering up {}".format(self._key))
        # TODO: check if OID for this socket is on
        self.redis_store.set(str(self._key) + '-outlet', '1')
