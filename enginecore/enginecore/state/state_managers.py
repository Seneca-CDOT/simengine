"""This file contains definitions of State Manager classes 

State managers provide interface for manipulating assets' states

Example: 
    a Server State Manager will contain server-specific logic for powering up/down a VM 
"""

import time
import os
import tempfile
import json
from enum import Enum

import redis
import libvirt
import pysnmp.proto.rfc1902 as snmp_data_types
from enginecore.model.graph_reference import GraphReference
import enginecore.model.system_modeler as sys_modeler

from enginecore.state.utils import format_as_redis_key
from enginecore.state.redis_channels import RedisChannels

class StateManager():
    """Base class for all the state managers """

    redis_store = None

    def __init__(self, asset_info, notify=False):
        self._graph_ref = GraphReference()
        self._asset_key = asset_info['key']
        self._asset_info = asset_info

        self._notify = notify

    @property
    def key(self):
        """Asset Key """
        return self._asset_key
    
    @property
    def redis_key(self):
        """Asset key in redis format as '{key}-{type}' """
        return "{}-{}".format(str(self.key), self.asset_type)

    @property
    def asset_type(self):
        """Asset Type """
        return self._asset_info['type']

    @property
    def power_usage(self):
        """Normal power usage in AMPS when powered up"""
        return 0

    @property
    def draw_percentage(self):
        """How much power the asset draws"""
        return self._asset_info['draw'] if 'draw' in self._asset_info else 1

    @property
    def load(self):
        """Get current load stored in redis (in AMPs)"""
        return float(StateManager.get_store().get(self.redis_key + ":load"))

    @property
    def wattage(self):
        return self.load * 120

    @property
    def status(self):
        """Operational State 
        
        Returns:
            int: 1 if on, 0 if off
        """
        return int(StateManager.get_store().get(self.redis_key))

    @property
    def agent(self):
        """Agent instance details (if supported)
        
        Returns:
            tuple: process id and status of the process (if it's running)
        """
        pid = StateManager.get_store().get(self.redis_key + ":agent")
        return (int(pid), os.path.exists("/proc/" + pid.decode("utf-8"))) if pid else None


    @agent.setter
    def agent(self, pid):
        StateManager.get_store().set(self.redis_key + ":agent", pid)


    def shut_down(self):
        """Implements state logic for graceful power-off event, sleeps for the pre-configured time
            
        Returns:
            int: Asset's status after power-off operation
        """
        print('Graceful shutdown')
        self._sleep_shutdown()
        if self.status:
            self._set_state_off()
        return self.status


    def power_off(self):
        """Implements state logic for abrupt power loss 
        
        Returns:
            int: Asset's status after power-off operation
        """
        print("Powering down {}".format(self._asset_key))
        if self.status:
            self._set_state_off()
        return self.status

    def power_up(self):
        """Implements state logic for power up, sleeps for the pre-configured time & resets boot time
        
        Returns:
            int: Asset's status after power-on operation
        """
        print("Powering up {}".format(self._asset_key))
        if self._parents_available() and not self.status:
            self._sleep_powerup()
            # udpate machine start time & turn on
            self.reset_boot_time()
            self._set_state_on()
        return self.status
 

    def update_load(self, load):
        """Update load """
        load = load if load >= 0 else 0
        StateManager.get_store().set(self.redis_key + ":load", load)
        self._publish_load()


    def reset_boot_time(self):
        """Reset the boot time to now"""
        StateManager.get_store().set(str(self._asset_key) + ":start_time", int(time.time())) 


    def get_config_off_delay(self):
        return NotImplementedError
    

    def get_config_on_delay(self):
        return NotImplementedError


    def _sleep_shutdown(self):
        if 'offDelay' in self._asset_info:
            time.sleep(self._asset_info['offDelay'] / 1000.0) # ms to sec


    def _sleep_powerup(self):
        if 'onDelay' in self._asset_info:
            time.sleep(self._asset_info['onDelay'] / 1000.0) # ms to sec
    

    def _set_state_on(self):
        StateManager.get_store().set(self.redis_key, '1')
        if self._notify:
            self.publish_power()


    def _set_state_off(self):
        StateManager.get_store().set(self.redis_key, '0')
        if self._notify:
            self.publish_power()


    def publish_power(self):
        """ publish state changes """
        StateManager.get_store().publish(RedisChannels.state_update_channel, self.redis_key)

    def _publish_load(self):
        """ publish load changes """
        StateManager.get_store().publish(RedisChannels.load_update_channel, self.redis_key)


    def _update_oid_value(self, oid, data_type, oid_value):
        """Update oid with a new value
        
        Args:
            oid(str): SNMP object id
            data_type(int): Data type in redis format
            oid_value(object): OID value in rfc1902 format 
        """
        redis_store = StateManager.get_store() 
        
        rvalue = "{}|{}".format(data_type, oid_value)
        rkey = format_as_redis_key(str(self._asset_key), oid, key_formatted=False)

        redis_store.set(rkey, rvalue)
        

    def _get_oid_value(self, oid, key):
        redis_store = StateManager.get_store() 
        rkey = format_as_redis_key(str(key), oid, key_formatted=False)
        return redis_store.get(rkey).decode().split('|')[1]


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
        
        not_affected_by_mains = True
        asset_keys, oid_keys = GraphReference.get_parent_keys(self._graph_ref.get_session(), self._asset_key)

        if not asset_keys and not StateManager.mains_status():
            not_affected_by_mains = False

        assets_up = self._check_parents(asset_keys, lambda rvalue, _: rvalue == b'0')
        oid_clause = lambda rvalue, rkey: rvalue.split(b'|')[1].decode() == oid_keys[rkey]['switchOff']
        oids_on = self._check_parents(oid_keys.keys(), oid_clause)

        return assets_up and oids_on and not_affected_by_mains
    

    @classmethod
    def get_temp_workplace_dir(cls):
        """Get location of the temp directory"""
        sys_temp = tempfile.gettempdir()
        simengine_temp = os.path.join(sys_temp, 'simengine')
        return simengine_temp
    

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
        .
        Returns:
            dict: Current information on assets including their states, load etc.
        """
        asset_keys = assets.keys()
        
        if not asset_keys:
            return None

        asset_values = cls.get_store().mget(
            list(map(lambda k: "{}-{}".format(k, assets[k]['type']), asset_keys))
        )

        for rkey, rvalue in zip(assets, asset_values):
            asset_state = StateManager(assets[rkey], assets[rkey]['type']) if assets[rkey]['type'] != 'ups' else UPSStateManager(assets[rkey])
            assets[rkey]['status'] = int(rvalue)
            assets[rkey]['load'] = asset_state.load
            if assets[rkey]['type'] == 'ups':
                assets[rkey]['battery'] = asset_state.battery_level
            
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
            assets = GraphReference.get_assets_and_connections(session, flatten)
            assets = cls._get_assets_states(assets, flatten)
            return assets


    @classmethod
    def reload_model(cls):
        """Request daemon reloading"""
        StateManager.get_store().publish(RedisChannels.model_update_channel, 'reload')

    
    @classmethod
    def power_outage(cls):
        """Simulate complete power outage/restoration"""
        StateManager.get_store().set('mains-source', '0')
        StateManager.get_store().publish(RedisChannels.mains_update_channel, '0')


    @classmethod
    def power_restore(cls):
        """Simulate complete power restoration"""
        StateManager.get_store().set('mains-source', '1')
        StateManager.get_store().publish(RedisChannels.mains_update_channel, '1')
    

    @classmethod
    def mains_status(cls):
        """Get wall power status"""
        return int(StateManager.get_store().get('mains-source').decode())


    @classmethod
    def get_ambient(cls):
        """Retrieve current ambient value"""
        temp = StateManager.get_store().get('ambient')
        return float(temp.decode()) if temp else 0


    @classmethod
    def set_ambient(cls, value):
        """Update ambient value"""
        old_temp = cls.get_ambient()
        StateManager.get_store().set('ambient', str(value))
        StateManager.get_store().publish(RedisChannels.ambient_update_channel, '{}-{}'.format(old_temp, value))  
    
    
    @classmethod
    def get_ambient_props(cls):
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


    @classmethod
    def get_state_manager_by_key(cls, key, supported_assets, notify=True):
        """Infer asset manager from key"""

        graph_ref = GraphReference()
        
        with graph_ref.get_session() as session:  
            asset_info = GraphReference.get_asset_and_components(session, key)
            return supported_assets[asset_info['type']].StateManagerCls(asset_info, notify=notify)


class UPSStateManager(StateManager):
    """Handles UPS state logic """


    class OutputStatus(Enum):
        """UPS output status """
        onLine = 1
        onBattery = 2
        off = 3
    
    class InputLineFailCause(Enum):
        """Reason for the occurrence of the last transfer to UPS """
        noTransfer = 1
        blackout = 2
        deepMomentarySag = 3
          
    def __init__(self, asset_info, notify=False):
        super(UPSStateManager, self).__init__(asset_info, notify)
        self._max_battery_level = 1000#%
        self._min_restore_charge_level = self._asset_info['minPowerOnBatteryLevel']
        self._full_recharge_time = self._asset_info['fullRechargeTime']


    @property
    def battery_level(self):
        """Get current level (high-precision)"""
        return int(StateManager.get_store().get(self.redis_key + ":battery").decode())


    @property
    def battery_max_level(self):
        """Max battery level"""
        return self._max_battery_level

    @property
    def wattage(self):
        return (self.load + self.idle_ups_amp) * self._asset_info['powerSource']

    @property
    def idle_ups_amp(self):
        """How much a UPS draws"""
        return self._asset_info['powerConsumption'] / self._asset_info['powerSource']

    @property
    def min_restore_charge_level(self):
        """min level of battery charge before UPS can be powered on"""
        return self._min_restore_charge_level
    
    @property
    def full_recharge_time(self):
        """hours taken to recharge the battery when it's completely depleted"""
        return self._full_recharge_time

    @property
    def output_capacity(self):
        """UPS rated capacity"""
        return self._asset_info['outputPowerCapacity']

    def update_temperature(self, temp):
        self._update_battery_temp_oid(temp + StateManager.get_ambient())

    def update_battery(self, charge_level):
        """Updates battery level, checks for the charge level being in valid range, sets battery-related OIDs
        and publishes changes;

        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """
        charge_level = 0 if charge_level < 0 else charge_level
        charge_level = self._max_battery_level if charge_level > self._max_battery_level else charge_level

        StateManager.get_store().set(self.redis_key + ":battery", int(charge_level))
        self._update_battery_oids(charge_level, self.battery_level)
        self._publish_battery()
    

    def update_load(self, load):
        """Update any load state associated with the device in the redis db 
        
        Args:
            load(float): New load in amps
        """
        super().update_load(load)
        if 'outputPowerCapacity' in self._asset_info:
            self._update_load_perc_oids(load)
            self._update_current_oids(load)
    

    def update_time_on_battery(self, timeticks):
        """Update OIDs associated with UPS time on battery
        
        Args:
            timeticks(int): time-on battery (seconds*100)
        """
        with self._graph_ref.get_session() as db_s:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'TimeOnBattery'
            )

            if oid:
                self._update_oid_value(oid, data_type, snmp_data_types.TimeTicks(timeticks))
    

    def update_time_left(self, timeticks):
        """Update OIDs associated with UPS runtime (estimation)
        
        Args:
            load(float): new load in AMPs
        """
        with self._graph_ref.get_session() as db_s:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'BatteryRunTimeRemaining'
            )

            if oid:
                self._update_oid_value(oid, data_type, snmp_data_types.TimeTicks(timeticks))

    def update_ups_output_status(self, status):
        with self._graph_ref.get_session() as db_s:
            oid, data_type, oid_spec = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'BasicOutputStatus'
            )
            
            if oid:
                self._update_oid_value(oid, data_type, snmp_data_types.Integer(oid_spec[status.name]))

    def update_transfer_reason(self, status):
        with self._graph_ref.get_session() as db_s:
            oid, data_type, oid_spec = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'InputLineFailCause'
            )
            
            if oid:
                self._update_oid_value(oid, data_type, snmp_data_types.Integer(oid_spec[status.name]))
    
    def _reset_power_off_oid(self):
        """Reset upsAdvControlUpsOff to 1 """
        with self._graph_ref.get_session() as session:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(session, int(self._asset_key), 'PowerOff')
            if oid:
                self._update_oid_value(oid, data_type, 1) # TODO: Can be something else
    
    def _update_current_oids(self, load):
        """Update OIDs associated with UPS Output - Current in AMPs
        
        Args:
            load(float): new load in AMPs
        """
        with self._graph_ref.get_session() as db_s:
            # 100%
            oid_adv, dt_adv, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvOutputCurrent')
            
            # 1000 (/10=%)
            oid_hp, dt_hp, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'HighPrecOutputCurrent'
            )

            if oid_adv:
                self._update_oid_value(oid_adv, dt_adv, snmp_data_types.Gauge32(load))
            if oid_hp:
                self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(load*10))


    def _update_load_perc_oids(self, load):
        """Update OIDs associated with UPS Output - % of the power capacity
        
        Args:
            load(float): new load in AMPs
        """

        power_capacity = self.output_capacity
        with self._graph_ref.get_session() as db_s:
            # 100%
            oid_adv, dt_adv, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvOutputLoad')
            
            # 1000 (/10=%)
            oid_hp, dt_hp, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'HighPrecOutputLoad'
            )

            value_hp = (1000*(load*120)) / power_capacity

            if oid_adv:
                self._update_oid_value(oid_adv, dt_adv, snmp_data_types.Gauge32(value_hp/10))
            if oid_hp:
                self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(value_hp))
            
    def _update_battery_temp_oid(self, temp):
        with self._graph_ref.get_session() as db_s:
            oid_hp, oid_dt, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'HighPrecBatteryTemperature'
            )

            self._update_oid_value(oid_hp, oid_dt, snmp_data_types.Gauge32(temp*10))

    def _update_battery_oids(self, charge_level, old_level):
        """Update OIDs associated with UPS Battery
        
        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """
        with self._graph_ref.get_session() as db_s:
            # 100%
            oid_adv, dt_adv, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvBatteryCapacity')
            # 1000 (/10=%)
            oid_hp, dt_hp, _ = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'HighPrecBatteryCapacity'
            )
            # low/good
            oid_basic, dt_basic, oid_spec = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), 'BasicBatteryStatus'
            )

            if oid_adv:
                self._update_oid_value(oid_adv, dt_adv, snmp_data_types.Gauge32(charge_level/10))
            if oid_hp:
                self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(charge_level))
            
            if oid_basic:
                if charge_level <= 100:
                    low_bat_value = oid_spec['batteryLow']
                    self._update_oid_value(oid_basic, dt_basic, snmp_data_types.Integer32(low_bat_value))
                elif old_level <= 100 and charge_level > 100:
                    norm_bat_value = oid_spec['batteryNormal']
                    self._update_oid_value(oid_basic, dt_basic, snmp_data_types.Integer32(norm_bat_value))


    def shut_down(self):
        time.sleep(self.get_config_off_delay())
        powered = super().shut_down()
        return powered

    def power_up(self):
        print("Powering up {}".format(self._asset_key))

        if self.battery_level and not self.status:
            self._sleep_powerup()
            time.sleep(self.get_config_on_delay())
            # udpate machine start time & turn on
            self.reset_boot_time()
            self._set_state_on()
        
        powered = self.status
        if powered:
            self._reset_power_off_oid()

        return powered


    def get_config_off_delay(self):
        with self._graph_ref.get_session() as db_s:
            oid, _, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvConfigShutoffDelay')
            return int(self._get_oid_value(oid, key=self._asset_key))


    def get_config_on_delay(self):
        with self._graph_ref.get_session() as db_s:
            oid, _, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvConfigReturnDelay')
            return int(self._get_oid_value(oid, key=self._asset_key))


    def _publish_battery(self):
        """Publish battery update"""
        StateManager.get_store().publish(RedisChannels.battery_update_channel, self.redis_key)
    

    def set_drain_speed_factor(self, factor):
        """Publish battery update"""
        rkey = "{}|{}".format(self.redis_key, factor)
        StateManager.get_store().publish(RedisChannels.battery_conf_drain_channel, rkey)
    

    def set_charge_speed_factor(self, factor):
        """Publish battery update"""
        rkey = "{}|{}".format(self.redis_key, factor)
        StateManager.get_store().publish(RedisChannels.battery_conf_charge_channel, rkey)

class PDUStateManager(StateManager):
    """Handles state logic for PDU asset """

    def __init__(self, asset_info, notify=False):
        super(PDUStateManager, self).__init__(asset_info, notify)
        

    def _update_current(self, load):
        """Update OID associated with the current amp value """
        with self._graph_ref.get_session() as session:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(session, int(self._asset_key), 'AmpOnPhase')
            if oid:
                load = load if load >= 0 else 0
                self._update_oid_value(oid, data_type, snmp_data_types.Gauge32(load * 10))
   

    def _update_wattage(self, wattage):
        """Update OID associated with the current wattage draw """
        with self._graph_ref.get_session() as session:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(session, int(self._asset_key), 'WattageDraw')
            wattage = wattage if wattage >= 0 else 0
            if oid:
                self._update_oid_value(oid, data_type, snmp_data_types.Integer32(wattage))


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

    class OutletState(Enum):
        """Outlet States (oid) """
        switchOff = 1
        switchOn = 2

    def __init__(self, asset_info, notify=False):
        super(OutletStateManager, self).__init__(asset_info, notify)

    def _get_oid_value_by_name(self, oid_name):
        """Get value under object id name"""
        with self._graph_ref.get_session() as session:
            oid, parent_key = GraphReference.get_component_oid_by_name(session, self.key, oid_name)
            if oid:
                oid = "{}.{}".format(oid, str(self.key)[-1])
                return int(self._get_oid_value(oid, key=parent_key))
            return 0

    def set_parent_oid_states(self, state):
        """Bulk-set parent oid values 
        
        Args:
            state(OutletState): new parent(s) state
        """
        with self._graph_ref.get_session() as session:
            _, oids = GraphReference.get_parent_keys(session, self._asset_key)
            oid_keys = oids.keys()
            parents_new_states = {}
            parent_values = StateManager.get_store().mget(oid_keys)
            
            for rkey, rvalue in zip(oid_keys, parent_values):
                #  datatype -> {} | {} <- value
                parents_new_states[rkey] = "{}|{}".format(rvalue.split(b'|')[0].decode(), oids[rkey][state.name])
            
            StateManager.get_store().mset(parents_new_states)

    def get_config_off_delay(self):
        return self._get_oid_value_by_name("OutletConfigPowerOffTime")


    def get_config_on_delay(self):
        return self._get_oid_value_by_name("OutletConfigPowerOnTime")


class StaticDeviceStateManager(StateManager):
    """Dummy Device that doesn't do much except drawing power """

    def __init__(self, asset_info, notify=False):
        super(StaticDeviceStateManager, self).__init__(asset_info, notify)


    @property
    def power_usage(self):
        return self._asset_info['powerConsumption'] / self._asset_info['powerSource']


    def power_up(self):
        powered = super().power_up()
        if powered:
            self.update_load(self.power_usage)
        return powered


class ServerStateManager(StaticDeviceStateManager):
    """Server state manager offers control over VM's state """

    def __init__(self, asset_info, notify=False):
        super(ServerStateManager, self).__init__(asset_info, notify)
        self._vm_conn = libvirt.open("qemu:///system")
        # TODO: error handling if the domain is missing (throws libvirtError) & close the connection
        self._vm = self._vm_conn.lookupByName(asset_info['domainName'])


    def vm_is_active(self):
        return self._vm.isActive()
    
    def shut_down(self):
        if self._vm.isActive():
            self._vm.destroy()
            self.update_load(0)
        return super().shut_down()


    def power_off(self):
        if self._vm.isActive():
            self._vm.destroy()
            self.update_load(0)
        return super().power_off()
    
    
    def power_up(self):
        powered = super().power_up()
        if not self._vm.isActive() and powered:
            self._vm.create()
            self.update_load(self.power_usage)
        return powered




class BMCServerStateManager(ServerStateManager):
    """Manage Server with BMC """

    def __init__(self, asset_info, notify=False):
        ServerStateManager.__init__(self, asset_info, notify)

    def power_up(self):
        powered = super().power_up()
        return powered


    def shut_down(self):
        return super().shut_down()


    def power_off(self):
        return super().power_off()


    def get_cpu_stats(self):
        """Get VM cpu stats (user_time, cpu_time etc. (see libvirt api)) """
        return self._vm.getCPUStats(True)


    @property
    def cpu_load(self):
        """Get latest recorded CPU load in percentage"""
        cpu_load = StateManager.get_store().get(self.redis_key + ":cpu_load")
        return int(cpu_load.decode()) if cpu_load else 0


    @cpu_load.setter
    def cpu_load(self, value):
        StateManager.get_store().set(self.redis_key + ":cpu_load", str(int(value)))


    @classmethod
    def get_sensor_definitions(cls, asset_key):
        """Get sensor definitions """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            return GraphReference.get_asset_sensors(session, asset_key)

    @classmethod
    def update_thermal_sensor_target(cls, attr):
        """Create new or update existing thermal relationship between 2 sensors"""
        new_rel = sys_modeler.set_thermal_sensor_target(attr)
        if new_rel: 
            StateManager.get_store().publish(
                RedisChannels.sensor_conf_th_channel, 
                json.dumps({
                    'key': attr['asset_key'],
                    'relationship': {
                        'source': attr['source_sensor'],
                        'target': attr['target_sensor'],
                        'event': attr['event']
                    }
                })
            ) 
    
    @classmethod
    def update_thermal_cpu_target(cls, attr):
        """Create new or update existing thermal relationship between CPU usage and sensor"""
        new_rel = sys_modeler.set_thermal_cpu_target(attr)
        if new_rel: 
            StateManager.get_store().publish(
                RedisChannels.cpu_usg_conf_th_channel, 
                json.dumps({
                    'key': attr['asset_key'],
                    'relationship': {
                        'target': attr['target_sensor'],
                    }
                })
            )  


class SimplePSUStateManager(StateManager):
    def __init__(self, asset_info, notify=False):
        StateManager.__init__(self, asset_info, notify)


class PSUStateManager(StateManager):


    def __init__(self, asset_info, notify=False):
        StateManager.__init__(self, asset_info, notify)
        self._psu_number = int(repr(asset_info['key'])[-1])
        # self._sensor = SensorRepository(int(repr(asset_info['key'])[:-1])).get


    def _update_current(self, load):
        """Update current inside state file """
        load = load if load >= 0 else 0
        # super()._write_sensor_file(super()._get_psu_current_file(self._psu_number), load)
    

    def _update_wattage(self, wattage):
        """Update wattage inside state file """        
        wattage = wattage if wattage >= 0 else 0    
        # super()._write_sensor_file(super()._get_psu_wattage_file(self._psu_number), wattage)


    def _update_fan_speed(self, value):
        """Speed In RPMs"""
        value = value if value >= 0 else 0    
        # super()._write_sensor_file(super()._get_psu_fan_file(self._psu_number), value)
    
        
    def set_psu_status(self, value):
        """0x08 indicates AC loss"""
        pass
        # if super().get_state_dir():
            # super()._write_sensor_file(super()._get_psu_status_file(self._psu_number), value)
    

    def update_load(self, load):
        super().update_load(load)
        min_load = self._asset_info['powerConsumption'] / self._asset_info['powerSource']
        
        # if super().get_state_dir():
        #     self._update_current(load + min_load)
        #     self._update_waltage((load + min_load) * 10)
        #     self._update_fan_speed(100 if load > 0 else 0)
