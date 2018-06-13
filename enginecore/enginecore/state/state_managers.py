""" This file contains definitions of Asset classes """

from circuits import Component
import redis
from enginecore.state.graph_reference import GraphReference

class StateManger():

    assets = {} # cache graph topology
    redis_store = None

    def __init__(self, key, asset_type):
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self._graph_db = GraphReference().get_session()
        self._asset_key = key
        self._asset_type = asset_type
    

    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()


    def power_down(self):
        """ Implements state logic for power down event """
        print("Powering down {}".format(self._asset_key))
        self.redis_store.set("{}-{}".format(str(self._asset_key), self._asset_type), '0')


    def power_up(self):
        """ Implements state logic for power up event """
        print("Powering up {}".format(self._asset_key))
        if self._parents_available():
            self.redis_store.set("{}-{}".format(str(self._asset_key), self._asset_type), '1')
 

    def _check_parents(self, keys, parent_down, msg='Cannot perform the action: [{}] parent is off'):
        """ Check that redis values pass certain condition
        
        Args:
            keys (list): Redis keys (formatted as required)
            parent_down (callable): lambda clause 
            msg (str, optional): Error message to be printed
        
        Returns: 
            bool: True if parent keys are missing or all parents were verified with parent_down clause 
        """
        if not keys:
            return True

        parent_values = self.redis_store.mget(keys)
        for rkey, rvalue in zip(keys, parent_values): 
            if parent_down(rvalue):
                print(msg.format(rkey))
                return False

        return True

    def _parents_available(self):
        """ Indicates whether a state action can be performed;
        checks if parent nodes are up & running and all OIDs indicate 'on' status
        
        Returns:
            bool: True if parents are available
        """
        asset_keys, oid_keys = GraphReference.get_parent_keys(self._graph_db, self._asset_key)
        
        assets_up = self._check_parents(asset_keys, lambda rvalue: rvalue == b'0')
        oids_on = self._check_parents(oid_keys, lambda rvalue: rvalue.split(b'|')[1] == b'0')

        return assets_up and oids_on
    
    
    @classmethod 
    def get_store(cls):
        if not cls.redis_store:
            cls.redis_store = redis.StrictRedis(host='localhost', port=6379)

        return cls.redis_store

    @classmethod 
    def _get_assets_states(cls, assets, flatten=True): 

        asset_keys = assets.keys()
        
        asset_values = cls.get_store().mget(
            list(map(lambda k: "{}-{}".format(k, assets[k]['type']), asset_keys))
        )

        for rkey, rvalue in zip(assets, asset_values):
            assets[rkey]['status'] = int(rvalue)
            if not flatten and 'children' in cls.assets[rkey]:
                assets[rkey]['children'] = cls._get_assets_states(assets[rkey]['children'])

        return assets

    @classmethod
    def get_system_status(cls, flatten=True):
        """Get states/status of all system components """
        with GraphReference().get_session() as session:

            # cache assets
            if not cls.assets:
                cls.assets = GraphReference.get_assets(session, flatten)

            cls.assets = cls._get_assets_states(cls.assets, flatten)
            return cls.assets

    @classmethod
    def get_asset_status(cls, asset_key):
        """Get state of an asset that has certain key """
        with GraphReference().get_session() as session: 
            asset = GraphReference.get_asset_and_components(session, asset_key)
            asset['status'] = int(cls.get_store().get("{}-{}".format(asset['key'], asset['type'])))
            return asset


class PDUStateManager(StateManger):
    """ Handles state logic for PDU asset """

    def __init__(self, key, asset_type='pdu'):
         super(PDUStateManager, self).__init__(key, asset_type)
        

class OutletStateManager(StateManger):
    """ Handles state logic for outlet asset """

    def __init__(self, key, asset_type='outlet'):
         super(OutletStateManager, self).__init__(key, asset_type)