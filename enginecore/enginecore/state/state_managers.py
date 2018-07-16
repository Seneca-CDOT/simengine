"""This file contains definitions of State Managers classes """

import time
import os
import pysnmp.proto.rfc1902 as snmp_data_types
import redis
import libvirt
from enginecore.model.graph_reference import GraphReference
from enginecore.state.utils import format_as_redis_key


class StateManager():

    assets = {} # cache graph topology
    redis_store = None

    def __init__(self, asset_info, asset_type, notify=False):
        self._graph_ref = GraphReference()
        self._asset_info = asset_info
        self._asset_type = asset_type
        self._notify = notify


    def get_key(self):
        """Asset Key """
        return self._asset_info['key']
    

    def get_type(self):
        """Asset Type """
        return self._asset_type

    def get_amperage(self):
        return 0

    def get_draw_percentage(self):
        return self._asset_info['draw'] if 'draw' in self._asset_info else 1

    
    def shut_down(self):
        """Implements state logic for graceful power-off event"""
        print('Graceful shutdown')
        self._sleep_shutdown()
        print (self.status())
        if self.status():
            self._set_state_off()
            self.update_load(0)
        return self.status()


    def power_off(self):
        """Implements state logic for abrupt power loss """
        print("Powering down {}".format(self._asset_info['key']))
        if self.status():
            self._set_state_off()
        return self.status()

    def power_up(self):
        """Implements state logic for power up event """
        print("Powering up {}".format(self._asset_info['key']))
        if self._parents_available() and not self.status():
            self._sleep_powerup()
            # udpate machine start time & turn on
            self.reset_boot_time()
            self._set_state_on()
        return self.status()
 
    def update_load(self, load):
        """ Update load """
        load = load if load >= 0 else 0
        StateManager.get_store().set(self._get_rkey() + ":load", load)
        self._publish_load(load)

    def get_load(self):
        """ Get load stored in redis (in AMPs)"""
        return float(StateManager.get_store().get(self._get_rkey() + ":load"))

    def status(self):
        """Operational State 
        
        Returns:
            int: 1 if on, 0 if off
        """
        return int(StateManager.get_store().get(self._get_rkey()))

    def reset_boot_time(self):
        """Reset the boot time to now"""
        StateManager.get_store().set(str(self._asset_info['key']) + ":start_time", int(time.time())) 

    def _sleep_shutdown(self):
        if 'offDelay' in self._asset_info:
            time.sleep(self._asset_info['offDelay'] / 1000.0) # ms to sec

    def _sleep_powerup(self):
        if 'onDelay' in self._asset_info:
            time.sleep(self._asset_info['onDelay'] / 1000.0) # ms to sec
    
    def _set_state_on(self):
        StateManager.get_store().set(self._get_rkey(), '1')
        if self._notify:
            self._publish_power()

    def _set_state_off(self):
        StateManager.get_store().set(self._get_rkey(), '0')
        if self._notify:
            self._publish_power()

    def _publish_power(self):
        """ publish state changes """
        StateManager.get_store().publish('state-upd', self._get_rkey())

    def _publish_load(self, load):
        """ publish load changes """
        StateManager.get_store().publish('load-upd', "{}-{}".format(self._asset_info['key'], load))

    def _update_oid(self, oid_details, oid_value):
        """Update oid with a new value
        
        Args:
            oid_details(dict): information about an object identifier stored in the graph ref
            oid_value(object): OID value in rfc1902 format 
        """
        redis_store = StateManager.get_store() 
        
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

        parent_values = StateManager.get_store().mget(keys)
        pdown = 0
        pdown_msg = ''
        for rkey, rvalue in zip(keys, parent_values): 
            if parent_down(rvalue, rkey):
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
        
        assets_up = self._check_parents(asset_keys, lambda rvalue, _: rvalue == b'0')
        oid_clause = lambda rvalue, rkey: rvalue.split(b'|')[1].decode() == oid_keys[rkey]['switchOff']
        oids_on = self._check_parents(oid_keys.keys(), oid_clause)

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
            assets[rkey]['load'] = StateManager(assets[rkey], assets[rkey]['type']).get_load()
            
            if not flatten and 'children' in assets[rkey]:
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
            assets = GraphReference.get_assets(session, flatten)
            assets = cls._get_assets_states(assets, flatten)
            return assets


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




class PDUStateManager(StateManager):
    """Handles state logic for PDU asset """

    def __init__(self, asset_info, asset_type='pdu', notify=False):
         super(PDUStateManager, self).__init__(asset_info, asset_type, notify)
        


    def _update_current(self, load):
        """Update OID associated with the current amp value """
        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {name: 'AmpOnPhase'}) return oid",
            key=int(self._asset_info['key'])
        )

        record = results.single()
        load = load if load >= 0 else 0
        if record:
            self._update_oid(record['oid'], snmp_data_types.Gauge32(load * 10))
   

    def _update_wattage(self, wattage):
        """Update OID associated with the current wattage draw """
        results = self._graph_ref.get_session().run(
            "MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {name: 'WattageDraw'}) return oid",
            key=int(self._asset_info['key'])
        )

        record = results.single()
        wattage = wattage if wattage >= 0 else 0
        if record:
            self._update_oid(record['oid'], snmp_data_types.Integer32(wattage))


    def update_load(self, load):
        """Update any load state associated with the device in the redis db 
        
        Args:
            load(float): New load in amps
        """
        super(PDUStateManager, self).update_load(load)
        self._update_current(load)
        self._update_wattage(load * 120)



class OutletStateManager(StateManager):
    """Handles state logic for outlet asset """

    def __init__(self, asset_info, asset_type='outlet', notify=False):
        super(OutletStateManager, self).__init__(asset_info, asset_type, notify)


class StaticDeviceStateManager(StateManager):
    """Dummy Device that doesn't do much except drawing power """

    def __init__(self, asset_info, asset_type='staticasset', notify=False):
        super(StaticDeviceStateManager, self).__init__(asset_info, asset_type, notify)

    def get_amperage(self):
        return self._asset_info['powerConsumption'] / self._asset_info['powerSource']


class ServerStateManager(StaticDeviceStateManager):
    """Server state manager offers control over VM's state """

    def __init__(self, asset_info, asset_type='server', notify=False):
        super(ServerStateManager, self).__init__(asset_info, asset_type, notify)
        self._vm_conn = libvirt.open("qemu:///system")
        # TODO: error handling if the domain is missing (throws libvirtError)
        self._vm = self._vm_conn.lookupByName(asset_info['name'])

    def shut_down(self):
        if self._vm.isActive():
            self._vm.shutdown()
        return super().shut_down()

    def power_off(self):
        if self._vm.isActive():
            self._vm.destroy()
        return super().power_off()
    
    def power_up(self):
        powered = super().power_up()
        if not self._vm.isActive() and powered:
            self._vm.create()
        self.update_load(self.get_amperage())
        return powered

class IPMIComponent():
    """ 
    PSU:
        IOUT_*: Current
        POUT_*: Power (Watts)
        VOUT_*: Voltage
    """
    def __init__(self, server_key):
        self._server_key = server_key
        self._sensor_dir = 'sensor_dir'

    def set_state_dir(self, state_dir):
        """Set temp state dir for an IPMI component"""
        StateManager.get_store().set(str(self._server_key)+ ":state_dir", state_dir)

    def get_state_dir(self):
        """Get temp IPMI state dir"""
        # TODO: raise if it doesn't exist
        return StateManager.get_store().get(str(self._server_key)+ ":state_dir").decode("utf-8")
    
    def _read_sensor_file(self, sensor_file):
        """Retrieve a single value representing sensor state"""
        with open(sensor_file) as sf_handler:
            return sf_handler.readline()
    
    def _write_sensor_file(self, sensor_file, data):
        """Update state of a sensor"""
        with open(sensor_file, 'w') as sf_handler:
            return sf_handler.write(str(int(data)) + '\n')

    def _get_psu_current_file(self, psu_id):
        """Get path to a file containing sensor current"""
        return os.path.join(self.get_state_dir(), os.path.join(self._sensor_dir, 'IOUT_{}'.format(psu_id)))
    
    def _get_psu_wattage_file(self, psu_id):
        """Get path to a file containing sensor wattage"""
        return os.path.join(self.get_state_dir(), os.path.join(self._sensor_dir, 'POUT_{}'.format(psu_id)))

class BMCServerStateManager(ServerStateManager, IPMIComponent):
    """Manage Server with BMC """
    def __init__(self, asset_info, asset_type='serverwithbmc', notify=False):
        ServerStateManager.__init__(self, asset_info, asset_type, notify)
        IPMIComponent.__init__(self, asset_info['key'])

class PSUStateManager(StateManager, IPMIComponent):

    def __init__(self, asset_info, asset_type='psu', notify=False):
        StateManager.__init__(self, asset_info, asset_type, notify)
        IPMIComponent.__init__(self,int(repr(asset_info['key'])[:-1]))
        self._psu_number = int(repr(asset_info['key'])[-1])
    
    def get_current(self):
        """Read current info from a sensor file """        
        return float(super()._read_sensor_file(super()._get_psu_current_file(self._psu_number)))

    def _update_current(self, load):
        """Update current inside state file """
        load = load if load >= 0 else 0
        super()._write_sensor_file(super()._get_psu_current_file(self._psu_number), load)
    
    def _update_waltage(self, wattage):
        """Update wattage inside state file """        
        wattage = wattage if wattage >= 0 else 0    
        super()._write_sensor_file(super()._get_psu_wattage_file(self._psu_number), wattage)

    def update_load(self, load):
        super().update_load(load)
        self._update_current(load)
        self._update_waltage(load * 120)