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

    def _check_parent_and_update(self, action):
        """ Perform action only if parent nodes are up & running
        Args:
            action(callable): action that needs to be done
        """
        asset_keys, oid_keys = GraphReference.get_parent_keys(self._graph_db, self._key)

        if asset_keys:
            parent_asset_values = self.redis_store.mget(asset_keys)
            for rkey, rvalue in zip(asset_keys, parent_asset_values):
                if rvalue == b'0':
                    print('Cannot perform the action: parent "{}" is offline'.format(rkey))
                    return
            
        if oid_keys:
            parent_oid_values = self.redis_store.mget(oid_keys)
            for rkey, rvalue in zip(oid_keys, parent_oid_values):
                _, oid_value = rvalue.split(b'|')
                if oid_value == b'0':
                    print('Cannot perform the action: parent OID "{}" is off'.format(rkey.replace(" ", "")))
                    return
            
        action()
            

class PDUStateManager(StateManger):
    

    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-pdu', '0')
    

    def power_up(self):
        print("Powering up {}".format(self._key))
        self._check_parent_and_update(
            lambda: self.redis_store.set(str(self._key) + '-pdu', '1')
        )
        

class OutletStateManager(StateManger):


    def power_down(self):
        print("Powering down {}".format(self._key))
        self.redis_store.set(str(self._key) + '-outlet', '0')


    def power_up(self):
        print("Powering up {}".format(self._key))

        self._check_parent_and_update(
            lambda: self.redis_store.set(str(self._key) + '-outlet', '1')
        )
