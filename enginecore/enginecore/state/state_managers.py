"""This file contains definitions of State Managers classes """

import time
import pysnmp.proto.rfc1902 as snmp_data_types
import redis
from enginecore.model.graph_reference import GraphReference
import enginecore.state.assets
from enginecore.state.utils import get_asset_type, format_as_redis_key


class StateManger():

    assets = {} # cache graph topology
    redis_store = None

    def __init__(self, asset_info, asset_type, notify=False):
        self._graph_ref = GraphReference()
        self._graph_db = self._graph_ref.get_session()
        self._asset_info = asset_info
        self._asset_type = asset_type
        self._notify = notify


    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()


    def get_key(self):
        """Asset Key """
        return self._asset_info['key']
    

    def get_type(self):
        """Asset Type """
        return self._asset_type

    def get_amperage(self):
        return 0

    
    def shut_down(self):
        """Implements state logic for graceful power-off event"""
        print('Graceful shutdown')
        if 'offDelay' in self._asset_info:
            time.sleep(self._asset_info['offDelay'] / 1000.0) # ms to sec
        self.power_off()


    def power_off(self):
        """Implements state logic for abrupt power loss """
        print("Powering down {}".format(self._asset_info['key']))
        if self.status():
            StateManger.get_store().set(self._get_rkey(), '0')
            if self._notify:
                self._publish()

        return self.status()

    def power_up(self):
        """Implements state logic for power up event """
        print("Powering up {}".format(self._asset_info['key']))
        if self._parents_available() and not self.status():
            if 'onDelay' in self._asset_info:
                time.sleep(self._asset_info['onDelay'] / 1000.0) # ms to sec
            # turn on & udpate machine start time
            StateManger.get_store().set(self._get_rkey(), '1')
            self.reset_boot_time()
            if self._notify:
                self._publish()

        return self.status()
 

    def calculate_load(self):
        """Calculate load for the device """
        raise NotImplementedError

    def update_load(self, load):
        """ Update load """
        if load >= 0:
            StateManger.get_store().set(self._get_rkey() + ":load", load)

    def get_load(self):
        """ Get load stored in redis """
        return float(StateManger.get_store().get(self._get_rkey() + ":load"))

    def status(self):
        """Operational State 
        
        Returns:
            int: 1 if on, 0 if off
        """
        return int(StateManger.get_store().get(self._get_rkey()))

    def reset_boot_time(self):
        """Reset the boot time to now"""
        StateManger.get_store().set(str(self._asset_info['key']) + ":start_time", int(time.time())) 

    def _publish(self):
        """ publish state changes """
        StateManger.get_store().publish('state-upd', self._get_rkey())


    def _update_oid(self, oid_details, oid_value):
        """Update oid with a new value
        
        Args:
            oid_details(dict): information about an object identifier stored in the graph ref
            oid_value(object): OID value in rfc1902 format 
        """
        redis_store = StateManger.get_store() 
        
        rvalue = "{}|{}".format(oid_details.get('dataType'), oid_value)
        rkey = format_as_redis_key(str(self._asset_info['key']), oid_details.get('OID'), key_formatted=False)

        redis_store.set(rkey, rvalue)
        

    def _get_rkey(self):
        """Get asset key in redis format"""
        return "{}-{}".format(str(self._asset_info['key']), self._asset_type)


    def _check_parents(self, keys, parent_down, msg='Cannot perform the action: [{}] parent is off'):
        """Check that redis values pass certain condition
        
        Args:
            keys (list): Redis keys (formatted as required)
            parent_down (callable): lambda clause 
            msg (str, optional): Error message to be printed
        
        Returns: 
            bool: True if parent keys are missing or all parents were verified with parent_down clause 
        """
        if not keys:
            return True

        parent_values = StateManger.get_store().mget(keys)
        pdown = 0
        pdown_msg = ''
        for rkey, rvalue in zip(keys, parent_values): 
            if parent_down(rvalue):
                pdown_msg += msg.format(rkey) + '\n'
                pdown += 1       
         
        if pdown == len(keys):
            print(pdown_msg)
            return False
        else:
            return True


    def _parents_available(self):
        """Indicates whether a state action can be performed;
        checks if parent nodes are up & running and all OIDs indicate 'on' status
        
        Returns:
            bool: True if parents are available
        """
        asset_keys, oid_keys = GraphReference.get_parent_keys(self._graph_ref.get_session(), self._asset_info['key'])
        
        assets_up = self._check_parents(asset_keys, lambda rvalue: rvalue == b'0')
        oids_on = self._check_parents(oid_keys, lambda rvalue: rvalue.split(b'|')[1] == b'0')

        return assets_up and oids_on
    
    
    @classmethod 
    def get_store(cls):
        """Get redis db handler """
        if not cls.redis_store:
            cls.redis_store = redis.StrictRedis(host='localhost', port=6379)

        return cls.redis_store

    @classmethod 
    def _get_assets_states(cls, assets, flatten=True): 
        """Query redis store and find states for each asset
        
        Args:
            flatten(bool): If false, the returned assets in the dict will have their child-components nested
        
        Returns:
            dict: Current information on assets including their states, load etc.
        """
        asset_keys = assets.keys()
        
        asset_values = cls.get_store().mget(
            list(map(lambda k: "{}-{}".format(k, assets[k]['type']), asset_keys))
        )

        for rkey, rvalue in zip(assets, asset_values):
            assets[rkey]['status'] = int(rvalue)
            assets[rkey]['load'] = cls.get_state_manager(assets[rkey]['type'])(assets[rkey]).get_load()
            
            if not flatten and 'children' in cls.assets[rkey]:
                # call recursively on children    
                assets[rkey]['children'] = cls._get_assets_states(assets[rkey]['children'])

        return assets


    @classmethod
    def get_system_status(cls, flatten=True):
        """Get states of all system components 
        
        Args:
            flatten(bool): If false, the returned assets in the dict will have their child-components nested
        
        Returns:
            dict: Current information on assets including their states, load etc.
        """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            # cache assets
            if not cls.assets:
                cls.assets = GraphReference.get_assets(session, flatten)

            cls.assets = cls._get_assets_states(cls.assets, flatten)
            return cls.assets


    @classmethod
    def get_asset_status(cls, asset_key):
        """Get state of an asset that has certain key 
        
        Args:
            asset_ket(string): asset key
        
        Returns:
            dict: asset detais
        """

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            asset = GraphReference.get_asset_and_components(session, asset_key)
            asset['status'] = int(cls.get_store().get("{}-{}".format(asset['key'], asset['type'])))
            return asset


    @classmethod 
    def get_state_manager(cls, asset_type):
        """Find StateManager class associated with an asset_type stored in graph db
        
        Args:
            asset_type(string): asset type
        
        Returns:
            class: State Manager class derived from StateManager
        """
        return enginecore.state.assets.SUPPORTED_ASSETS[asset_type].StateManagerCls


class PDUStateManager(StateManger):
    """Handles state logic for PDU asset """

    def __init__(self, asset_info, asset_type='pdu', notify=False):
         super(PDUStateManager, self).__init__(asset_info, asset_type, notify)
        

    def calculate_load(self, exclude=False):
        """Find PDU load by querying each outlet's load
        Note that this function will traverse the graph & calculate load for every device down the power chain

        Args:
            exclude(string): asset key of the outlet excluded from query
        
        Returns:
            float: load in amps
        """

        if not self.status():
            return 0

        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })<-[:POWERED_BY]-(asset:Asset) RETURN asset",
            key=int(self._asset_info['key'])
        )

        load = 0
        for record in results:
            if exclude != record['asset'].get('key'):
                outlet_manager = OutletStateManager(dict(record['asset']))
                load += outlet_manager.calculate_load()

        return load


    def _update_current(self, load):
        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {name: 'AmpOnPhase'}) return oid",
            key=int(self._asset_info['key'])
        )

        record = results.single()
        if record and load >= 0:
            self._update_oid(record['oid'], snmp_data_types.Gauge32(load * 10))
   

    def _update_wattage(self, wattage):
        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {name: 'WattageDraw'}) return oid",
            key=int(self._asset_info['key'])
        )

        record = results.single()

        if record and wattage >= 0:
            self._update_oid(record['oid'], snmp_data_types.Integer32(wattage))


    def update_load(self, load):
        """Update any load state associated with the device in the redis db 
        
        Args:
            load(float): New load in amps
        """
        super(PDUStateManager, self).update_load(load)
        self._update_current(load)
        self._update_wattage(load * 120)



class OutletStateManager(StateManger):
    """Handles state logic for outlet asset """

    def __init__(self, asset_info, asset_type='outlet', notify=False):
        super(OutletStateManager, self).__init__(asset_info, asset_type, notify)

    def calculate_load(self):
        """Find what kind of device the outlet powers & return load of that device 
        Note that this function will traverse the graph & calculate load for every device down the power chain
        
        Returns:
            float: outlet load in amps
        """
        
        if not self.status():
            return 0

        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })<-[:POWERED_BY]-(asset:Asset) RETURN asset, labels(asset) as labels",
            key=int(self._asset_info['key'])
        )

        record = results.single()
        load = 0
        
        if record:
            asset_type = get_asset_type(record['labels'])
            load = self.get_state_manager(asset_type)(dict(record['asset'])).calculate_load()
        
        return load



class StaticDeviceStateManager(StateManger):
    """Dummy Device that doesn't do much except drawing power """

    def __init__(self, asset_info, asset_type='staticasset', notify=False):
        super(StaticDeviceStateManager, self).__init__(asset_info, asset_type, notify)

    def get_amperage(self):
        return self._asset_info['powerConsumption'] / self._asset_info['powerSource']
    
    def calculate_load(self):
        """Calculate load in AMPs 
        
        Returns:
            float: device load in amps
        """
        return self.get_amperage() if self.status() else 0

class ServerStateManager(StaticDeviceStateManager):
    """Server state manager offers control over VM's state """

    def __init__(self, asset_info, asset_type='server', notify=False):
        super(ServerStateManager, self).__init__(asset_info, asset_type, notify)


class PSUStateManager(StateManger):
    def __init__(self, asset_info, asset_type='psu', notify=False):
        super(PSUStateManager, self).__init__(asset_info, asset_type, notify)