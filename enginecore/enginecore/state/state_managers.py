""" This file contains definitions of Asset classes """

from circuits import Component
import redis
from enginecore.state.graph_reference import GraphReference
import enginecore.state.assets
from enginecore.state.utils import get_asset_type

class StateManger():

    assets = {} # cache graph topology
    redis_store = None

    def __init__(self, asset_info, asset_type):
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self._graph_db = GraphReference().get_session()
        self._asset_info = asset_info
        self._asset_type = asset_type

    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()

    def get_key(self):
        return self._asset_info['key']

    def power_down(self):
        """ Implements state logic for power down event """
        print("Powering down {}".format(self._asset_info['key']))
        if self.status():
            self.redis_store.set("{}-{}".format(str(self._asset_info['key']), self._asset_type), '0')


    def power_up(self):
        """ Implements state logic for power up event """
        print("Powering up {}".format(self._asset_info['key']))
        if self._parents_available():
            self.redis_store.set("{}-{}".format(str(self._asset_info['key']), self._asset_type), '1')
 
    def get_load(self):
        """ Calculate load for the device """
        pass
    
    def status(self):
        return int(self.redis_store.get("{}-{}".format(str(self._asset_info['key']), self._asset_type)))



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
        asset_keys, oid_keys = GraphReference.get_parent_keys(self._graph_db, self._asset_info['key'])
        
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
        """ Query redis store and find states for each asset """
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

    def __init__(self, asset_info, asset_type='pdu'):
         super(PDUStateManager, self).__init__(asset_info, asset_type)
        
    def get_load(self):

        if not self.status():
            return 0

        # query the graph db and find info about outlets (or use subscript for key)
        # call on OutletStateManager(asset_key).get_load() - can be multithreaded
        results = self._graph_db.run(
            "MATCH (:Asset { key: $key })<-[:POWERED_BY]-(asset:Asset) RETURN asset",
            key=int(self._asset_info['key'])
        )

        load = 0
        for record in results:
            om = OutletStateManager(dict(record['asset']))
            load += om.get_load()

        return load

class OutletStateManager(StateManger):
    """ Handles state logic for outlet asset """

    def __init__(self, asset_info, asset_type='outlet'):
         super(OutletStateManager, self).__init__(asset_info, asset_type)

    def get_load(self):
        # query the graph db and find what outlet 'powers' (o)<-[:POWERED_BY]-(d)
        
        if not self.status():
            return 0
        results = self._graph_db.run(
            "MATCH (:Asset { key: $key })<-[:POWERED_BY]-(asset:Asset) RETURN asset, labels(asset) as labels",
            key=int(self._asset_info['key'])
        )

        record = results.single()
        load = 0
        
        if record:
            asset_type = get_asset_type(record['labels'])
            load = enginecore.state.assets.SUPPORTED_ASSETS[asset_type].StateManagerCls(dict(record['asset'])).get_load()
        
        return load



class StaticDeviceStateManager(StateManger):
    def __init__(self, asset_info, asset_type='staticasset'):
        super(StaticDeviceStateManager, self).__init__(asset_info, asset_type)
        self._asset = GraphReference.get_asset_and_components(self._graph_db, asset_info['key'])
    
    def get_load(self):
        return self._asset['powerConsumption'] / self._asset['powerSource'] if self.status() else 0
