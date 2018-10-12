"""This file contains definitions of Assets 

Each asset class contains reactive logic associated with certain events. 

Example:
    a PDU asset will be instantiated if there's a node labeled as "PDU" in a graph db (:PDU),
    isntance of a PDU asset can react to upstream power loss or any other event defined 
    as a handler. It can also wrap SNMPAgent if supported.

"""
# **due to circuit callback signature
# pylint: disable=W0613

import subprocess
import os
import pwd
import grp
import tempfile
import atexit
import json
import time
import sysconfig
from threading import Thread
from collections import namedtuple
import datetime as dt
from distutils.dir_util import copy_tree
from string import Template

from circuits import Component, handler
import enginecore.state.state_managers as sm
from enginecore.state.asset_definition import register_asset, SUPPORTED_ASSETS

PowerEventResult = namedtuple("PowerEventResult", "old_state new_state asset_key asset_type")
PowerEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)
LoadEventResult = namedtuple("LoadEventResult", "load_change old_load new_load asset_key asset_type")
LoadEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)


class SystemEnvironment(Component):
    """Represents hardware's environment (Room/ServerRack)"""
    
    def __init__(self):
        super(SystemEnvironment, self).__init__()

        # threads to track
        self._temp_warming_t = None
        self._temp_cooling_t = None

        # Set defaults 
        self._outage_temp_increase = 2
        self._outage_temp_rate = 60 * 6 # every 6 minutes 
        self._outage_temp_max = 34

        self._ac_on_temp_decrease = 1
        self._ac_on_temp_rate = 60 * 6 # every 6 minutes 
        self._ac_on_temp_min = 21


    @property
    def outage_temp_increase(self):
        """Temperature increase per rate (upon outage)"""
        return self._outage_temp_increase
    
    
    @outage_temp_increase.setter
    def outage_temp_increase(self, value):
        self._outage_temp_increase = value


    @property
    def outage_temp_rate(self):
        """Rate in seconds (upon outage)"""
        return self._outage_temp_rate


    @outage_temp_rate.setter
    def outage_temp_rate(self, value):
        if value <= 0:
            raise ValueError  
        
        self._outage_temp_rate = value


    @property
    def outage_temp_max(self):
        """Maxium room temperature that can be reached (outage)"""
        return self._outage_temp_max
    

    @outage_temp_max.setter
    def outage_temp_max(self, value):
        self._outage_temp_max = value


    @property
    def ac_on_temp_decrease(self):
        """Temperature drop value per N num of seconds (when AC is on)"""
        return self._ac_on_temp_decrease
    
    
    @ac_on_temp_decrease.setter
    def ac_on_temp_decrease(self, value):
        self._ac_on_temp_decrease = value
    

    @property
    def ac_on_temp_rate(self):
        """Rate in seconds (when AC is on)"""
        return self._ac_on_temp_rate


    @ac_on_temp_rate.setter
    def ac_on_temp_rate(self, value):
        if value <= 0:
            raise ValueError  
        
        self._ac_on_temp_rate = value


    @property
    def ac_on_temp_min(self):
        """Miminum room temperature value that can be reached with AC cooling"""
        return self._ac_on_temp_min
    

    @ac_on_temp_min.setter
    def ac_on_temp_min(self, value):
        self._ac_on_temp_min = value


    def _keep_changing_temp(self, thermal_cond, update_cond, sleep_duration, calc_temp_op):
        """Change room temperature until limit is reached or AC state changes
        
        Args:
            thermal_cond(callable): update room temp while the condition remains true
            update_cond(callable): 
            sleep_duration(callable): update every 'n' seconds
            calc_temp_op(callable): calculate new temperature
        """
        
        room_temp = sm.StateManager.get_ambient()
        print("s",room_temp)
        
        while thermal_cond():
            print(sleep_duration())
            time.sleep(sleep_duration())
            room_temp = calc_temp_op()
            print("w",room_temp)
            if update_cond(room_temp):   
                print(room_temp)
                sm.StateManager.set_ambient(room_temp)


    def _launch_temp_warming(self):
        """Start the process of raising ambient"""

        self._temp_warming_t = Thread(
            target=self._keep_changing_temp,
            kwargs={
                'thermal_cond': lambda: not sm.StateManager.mains_status(), 
                'update_cond':  lambda r_temp: r_temp <= self._outage_temp_max,
                'sleep_duration': lambda: self._outage_temp_rate, # temp increase per num of seconds
                'calc_temp_op': lambda: sm.StateManager.get_ambient() + self._ac_on_temp_decrease # temp increase 
            },
            name="temp_warming"
        )
        self._temp_warming_t.daemon = True
        self._temp_warming_t.start()


    def _launch_temp_cooling(self):
        """Start the process of cooling room temperature"""

        self._temp_cooling_t = Thread(
            target=self._keep_changing_temp,
            kwargs={
                'thermal_cond': sm.StateManager.mains_status,
                'update_cond': lambda r_temp: r_temp >= self._ac_on_temp_min,
                'sleep_duration': lambda: self._ac_on_temp_rate, # temp change per num of seconds
                'calc_temp_op': lambda: sm.StateManager.get_ambient() - self._ac_on_temp_decrease # temp change 
            }, 
            name="temp_cooling"
        )
        self._temp_cooling_t.daemon = True
        self._temp_cooling_t.start()


    @handler("PowerOutage")
    def on_power_outage(self):
        """Handle power outage - start warming up the room"""
        print('launch')
        self._launch_temp_warming()


    @handler("PowerRestored")
    def on_power_restored(self):
        """Handle power restoration - start cooling down the room"""
        self._launch_temp_cooling()
        

class Asset(Component):
    """Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self.state.reset_boot_time()
        self.state.update_load(0)

    @property
    def key(self):
        """ Get ID assigned to the asset """
        return self.state.key

    @property
    def state(self):
        """State manager instance"""
        return self._state
    
    def power_up(self):
        """Power up this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key, 
            asset_type=self.state.asset_type, 
            old_state=old_state,
            new_state=self.state.power_up()
        )

    def shut_down(self):
        """Shut down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key, 
            asset_type=self.state.asset_type, 
            old_state=old_state,
            new_state=self.state.shut_down()
        )

    def power_off(self):
        """Power down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self.state.key, 
            asset_type=self.state.asset_type, 
            old_state=old_state,
            new_state=self.state.power_off()
        )

    def _update_load(self, load_change, arithmetic_op, msg=''):
        """React to load changes by updating asset load
        
        Args:
            load_change(float): how much AMPs need to be added/subtracted
            arithmetic_op(callable): calculates new load (receives old load & measured load change)
            msg(str): message to be printed
        
        Returns:
            LoadEventResult: Event result containing old & new load values as well as value subtracted/added
        """
        
        old_load = self.state.load
        new_load = arithmetic_op(old_load, load_change)
        
        if msg:
            print(msg.format(self.state.key, old_load, load_change, new_load))
        
        self.state.update_load(new_load)

        return LoadEventResult(
            load_change=load_change,
            old_load=old_load,
            new_load=new_load,
            asset_key=self.state.key
        )

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased")
    def on_load_increase(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        Returns: 
            LoadEventResult: details on the asset state updates
        """
        
        increased_by = kwargs['child_load']
        msg = 'Asset : {} : orig load {}, increased by: {}, new load: {}'
        return self._update_load(increased_by, lambda old, change: old+change, msg)

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        decreased_by = kwargs['child_load']
        msg = 'Asset : {} : orig load {}, decreased by: {}, new load: {}'
        return self._update_load(decreased_by, lambda old, change: old-change, msg)

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS

    @classmethod
    def get_state_manager_by_key(cls, key, notify=True):
        """Get a state manager specific to the asset type
        Args:
            key(int): asset key
        Returns:
            StateManager: instance of the StateManager sub-class
        """
        return sm.StateManager.get_state_manager_by_key(key, cls.get_supported_assets(), notify)

class Agent():
    """Abstract Agent Class """
    agent_num = 1    
    

    def __init__(self):
        self._process = None


    def start_agent(self):
        """Logic for starting up the agent """
        raise NotImplementedError


    @property
    def pid(self):
        """Get agent process id"""
        return self._process.pid


    def stop_agent(self):
        """Logic for agent's termination """
        if not self._process.poll():
            self._process.kill()
    

    def register_process(self, process):
        """Set process instance
        Args:
            process(Popen): process to be managed
        """
        self._process = process
        atexit.register(self.stop_agent)
    

class IPMIAgent(Agent):
    """IPMIsim instance """

    supported_sensors = {
        'caseFan': '',
        'psuStatus': '',
        'psuVoltage': '',
        'psuPower': '',
        'psuCurrent': ''
    }

    def __init__(self, key, ipmi_dir, ipmi_config, sensors):
        super(IPMIAgent, self).__init__()
        self._asset_key = key
        self._ipmi_dir = ipmi_dir

        
        copy_tree(os.environ.get('SIMENGINE_IPMI_TEMPL'), self._ipmi_dir)

        # sensor, emu & lan configuration file paths
        lan_conf = os.path.join(self._ipmi_dir, 'lan.conf')
        ipmisim_emu = os.path.join(self._ipmi_dir, 'ipmisim1.emu')
        sdr_main = os.path.join(*[self._ipmi_dir, 'emu_state', 'ipmi_sim', 'ipmisim1', 'sdr.20.main'])
        sensor_def = os.path.join(self._ipmi_dir, 'main.sdrs')
        sensor_dir = os.path.join(self._ipmi_dir, 'sensor_dir')


        lib_path = os.path.join(sysconfig.get_config_var('LIBDIR'), "simengine", 'haos_extend.so')
        
        # Template options
        lan_conf_opt = {
            'asset_key': key, 
            'extend_lib': lib_path,
            'host': ipmi_config['host'],
            'port': ipmi_config['port'],
            'user': ipmi_config['user'],
            'password': ipmi_config['password'],
            'vmport':  ipmi_config['vmport']
        }

        ipmisim_emu_opt = {
            **{
                'ipmi_dir': self._ipmi_dir, 
            },
            **IPMIAgent.supported_sensors
        }
        
        main_sdr_opt = {
            **{
                'ipmi_dir': self._ipmi_dir, 
                'includes': '',
            },
            **IPMIAgent.supported_sensors
        }

        # initialize sensors
        for i, sensor in enumerate(sensors):
            print(sensor)

            s_specs = sensor['specs']
            
            if 'index' in s_specs:
                s_idx = hex(int(sensor['address_space']['address'], 16) + s_specs['index']) 
            else:
                s_idx = s_specs['address']

            sensor_file = "{}_{}".format(s_specs['type'], s_idx)

            with open(os.path.join(sensor_dir, sensor_file), "w+") as filein:
                filein.write(str(int(s_specs['defaultValue']*0.1) if 'defaultValue' in s_specs else 0))
            

            index = str(s_specs['index']+1)if 'index' in s_specs else ''

            main_sdr_opt[s_specs['type']] += 'define IDX "{}" \n'.format(index)

            main_sdr_opt[s_specs['type']] += 'define ID_STR "{}" \n'.format(i)
            main_sdr_opt[s_specs['type']] += 'define ADDR "{}" \n'.format(s_idx)

            main_sdr_opt[s_specs['type']] += 'define LNR "{}"  \n'.format(s_specs['lnr'] if 'lnr' in s_specs else 0)
            main_sdr_opt[s_specs['type']] += 'define LCR "{}"  \n'.format(s_specs['lcr'] if 'lcr' in s_specs else 0)
            main_sdr_opt[s_specs['type']] += 'define LNC "{}"  \n'.format(s_specs['lnc'] if 'lnc' in s_specs else 0)
            main_sdr_opt[s_specs['type']] += 'define UNC "{}"  \n'.format(s_specs['unc'] if 'unc' in s_specs else 0)
            main_sdr_opt[s_specs['type']] += 'define UCR "{}"  \n'.format(s_specs['ucr'] if 'ucr' in s_specs else 0)
            main_sdr_opt[s_specs['type']] += 'define UNR "{}"  \n'.format(s_specs['unr'] if 'unr' in s_specs else 0)
            
            # Specify if sensor values should be returned:
            main_sdr_opt[s_specs['type']] += 'define R_LNR "{}"  \n'.format('lnr' in s_specs)
            main_sdr_opt[s_specs['type']] += 'define R_LCR "{}"  \n'.format('lcr' in s_specs)
            main_sdr_opt[s_specs['type']] += 'define R_LNC "{}"  \n'.format('lnc' in s_specs)
            main_sdr_opt[s_specs['type']] += 'define R_UNC "{}"  \n'.format('unc' in s_specs)
            main_sdr_opt[s_specs['type']] += 'define R_UCR "{}"  \n'.format('ucr' in s_specs)
            main_sdr_opt[s_specs['type']] += 'define R_UNR "{}"  \n'.format('unr' in s_specs)
            
            s_name = s_specs['name'].format(index='"$IDX"')

            main_sdr_opt[s_specs['type']] += 'define C_NAME "{}" \n'.format(s_name)
            main_sdr_opt[s_specs['type']] += 'include "{}/{}.sdrs" \n'.format(self._ipmi_dir, s_specs['type'])

            #  0x20  0   0x74    3     1 
            e_type = s_specs['eventReadingType'] if 'eventReadingType' in s_specs else 1

            ipmisim_emu_opt[s_specs['type']] += 'sensor_add 0x20  0   {}   3     {} poll 2000 '.format(s_idx, e_type)
            ipmisim_emu_opt[s_specs['type']] += 'file $TEMP_IPMI_DIR"/sensor_dir/{}" \n'.format(sensor_file)
        
        print(main_sdr_opt)

        # Set server-specific includes
        if ipmi_config['num_components'] == 2:
            ipmisim_emu_opt['includes'] = 'include "{}"'.format(os.path.join(self._ipmi_dir, 'ipmisim1_psu.emu'))
            main_sdr_opt['includes'] = 'include "{}"'.format(os.path.join(self._ipmi_dir, 'main_dual_psu.sdrs'))

        # Substitute a template
        self._substitute_template_file(lan_conf, lan_conf_opt)
        self._substitute_template_file(ipmisim_emu, ipmisim_emu_opt)
        self._substitute_template_file(sensor_def, main_sdr_opt)

        # compile sensor definitions
        os.system("sdrcomp -o {} {}".format(sdr_main, sensor_def))
        subprocess.call(['chmod', '-R', 'ugo+rwx', self._ipmi_dir])
        self.start_agent()
        IPMIAgent.agent_num += 1


    def _substitute_template_file(self, filename, options):
        """Update file using python templating """
        with open(filename, "r+", encoding="utf-8") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(options))


    def start_agent(self):
        """ Logic for starting up the agent """

        # start a new one
        lan_conf = os.path.join(self._ipmi_dir, 'lan.conf')
        ipmisim_emu = os.path.join(self._ipmi_dir, 'ipmisim1.emu')
        state_dir = os.path.join(self._ipmi_dir, 'emu_state')

        cmd = ["ipmi_sim",
               "-c", lan_conf,
               "-f", ipmisim_emu,
               "-s", state_dir,
               "-n"]

        print(' '.join(cmd))

        self.register_process(subprocess.Popen(
            cmd, stderr=subprocess.DEVNULL, close_fds=True
        ))

        print("Started ipmi_sim process under pid {}".format(self._process.pid))


    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_agent()


class SNMPAgent(Agent):
    """SNMP simulator instance """

    def __init__(self, key, host, port, public_community='public', private_community='private', lookup_oid='1.3.6'):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key

        # set up community strings
        self._snmp_rec_public_fname = public_community + '.snmprec'
        self._snmp_rec_private_fname = private_community + '.snmprec'

        sys_temp = tempfile.gettempdir()
        simengine_temp = os.path.join(sys_temp, 'simengine')
        
        self._snmp_rec_dir = os.path.join(simengine_temp, str(key))
        os.makedirs(self._snmp_rec_dir)
        self._host = '{}:{}'.format(host, port)
        
        # snmpsimd.py will be run by a user 'nobody'
        uid = pwd.getpwnam("nobody").pw_uid
        gid = grp.getgrnam("nobody").gr_gid
        
        # change ownership
        os.chown(self._snmp_rec_dir, uid, gid)
        snmp_rec_public_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_public_fname)
        snmp_rec_private_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_private_fname)

        # get location of the lua script that will be executed by snmpsimd
        redis_script_sha = os.environ.get('SIMENGINE_SNMP_SHA')
        snmpsim_config = "{}|:redis|key-spaces-id={},evalsha={}\n".format(lookup_oid, key, redis_script_sha)

        with open(snmp_rec_public_filepath, "a") as tmp_pub, open(snmp_rec_private_filepath, "a") as tmp_priv:
            tmp_pub.write(snmpsim_config)
            tmp_priv.write(snmpsim_config)
            
        self.start_agent()

        SNMPAgent.agent_num += 1


    def start_agent(self):
        """Logic for starting up the agent """

        log_file = os.path.join(self._snmp_rec_dir, "snmpsimd.log")
        
        # start a new one
        cmd = ["snmpsimd.py", 
               "--agent-udpv4-endpoint={}".format(self._host),
               "--variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id),
               "--data-dir="+self._snmp_rec_dir,
               "--transport-id-offset="+str(SNMPAgent.agent_num),
               "--process-user=nobody",
               "--process-group=nobody",
               # "--daemonize",
               "--logging-method=file:"+log_file
              ]

        print(' '.join(cmd))
        self.register_process(subprocess.Popen(
            cmd, stderr=subprocess.DEVNULL, close_fds=True
        ))
    
        print("Started SNMPsim process under pid {}".format(self._process.pid))


class SNMPSim():
    
    def __init__(self, key, host, port):
        self._snmp_agent = SNMPAgent(key, host, port)


    ##### Create/kill SNMP agent when state changes
    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        self._snmp_agent.stop_agent()


    @handler("ButtonPowerUpPressed", "ParentAssetPowerUp")
    def on_asset_did_power_on(self):
        self._snmp_agent.start_agent()

@register_asset
class PDU(Asset, SNMPSim):
    """Provides reactive logic for PDU & manages snmp simulator instance
    Example:
        powers down when upstream power becomes unavailable 
        powers back up when upstream power is restored
    """

    channel = "engine-pdu"
    StateManagerCls = sm.PDUStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, PDU.StateManagerCls(asset_info))
        # Run snmpsim instance
        SNMPSim.__init__(
            self, 
            key=asset_info['key'],
            host=asset_info['host'] if 'host' in asset_info else 'localhost',
            port=asset_info['port'] if 'port' in asset_info else 161
        )

        self.state.agent = self.pid


    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Power off & stop snmp simulator instance when parent is down"""

        e_result = self.power_off()
        
        if e_result.new_state == e_result.old_state:
            event.success = False
        else:
            self._snmp_agent.stop_agent()

        return e_result


    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """Power up PDU when upstream power source is restored """
        e_result = self.power_up()
        event.success = e_result.new_state != e_result.old_state

        return e_result


@register_asset
class UPS(Asset, SNMPSim):
    """Provides reactive logic for UPS & manages snmp simulator instance

    Example:
        drains battery when upstream power becomes unavailable 
        charges battery when upstream power is restored
    """

    channel = "engine-ups"
    StateManagerCls = sm.UPSStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, UPS.StateManagerCls(asset_info))
        SNMPSim.__init__(
            self, 
            key=asset_info['key'],
            host=asset_info['host'] if 'host' in asset_info else 'localhost',
            port=asset_info['port'] if 'port' in asset_info else 161
        )

        self.state.agent = self.pid

        # Store known { wattage: time_remaining } key/value pairs (runtime graph)
        self._runtime_details = json.loads(asset_info['runtime'])

        # Track upstream power availability
        self._parent_up = True
        self._charge_speed_factor = 1
        self._drain_speed_factor = 1

        # Threads responsible for battery charge/discharge
        self._battery_drain_t = None
        self._battery_charge_t = None

        self._start_time_battery = None

        # set battery level to max
        self.state.update_battery(self.state.battery_max_level)
        
        # get charge per second using full recharge time (hrs)
        self._charge_per_second = self.state.battery_max_level / (self.state.full_recharge_time*60*60)

        # set temp on start
        self._state.update_temperature(7)


    def _cacl_time_left(self, wattage):
        """Approximate runtime estimation based on current battery level""" 
        return (self._calc_full_power_time_left(wattage)*self.state.battery_level)/self.state.battery_max_level


    def _calc_full_power_time_left(self, wattage):
        """Approximate runtime estimation for the fully-charged battery""" 
        close_wattage = min(self._runtime_details, key=lambda x: abs(int(x)-wattage))
        close_timeleft = self._runtime_details[close_wattage]
        return (close_timeleft * int(close_wattage)) / wattage # inverse proportion


    def _calc_battery_discharge(self):
        """Approximate battery discharge per second based on the runtime model & current wattage draw

        Returns:
            float: discharge per second 
        """
        # return 100
        wattage = self.state.wattage
        fp_estimated_timeleft = self._calc_full_power_time_left(wattage)
        return self.state.battery_max_level / (fp_estimated_timeleft*60)


    def _drain_battery(self, parent_up):
        """When parent is not available -> drain battery 
        
        Args:
            parent_up(callable): indicates if the upstream power is available
        """

        battery_level = self.state.battery_level
        blackout = False

        # keep draining battery while its level remains above 0, UPS is on and parent is down
        while battery_level > 0 and self.state.status and not parent_up():

            # calculate new battery level
            battery_level = battery_level - (self._calc_battery_discharge() * self._drain_speed_factor)
            seconds_on_battery = (dt.datetime.now() - self._start_time_battery).seconds
            
            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(self._cacl_time_left(self.state.wattage) * 60 * 100)
            self.state.update_time_on_battery(seconds_on_battery * 100)
            
            if seconds_on_battery > 5 and not blackout:
                blackout = True
                self.state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.blackout)
            
            time.sleep(1)
        
        # kill the thing if still breathing
        if self.state.status and not parent_up():
            self._snmp_agent.stop_agent()
            self.state.power_off()
            self.state.publish_power()


    def _charge_battery(self, parent_up, power_up_on_charge=False):
        """Charge battery when there's upstream power source & battery is not full
                
        Args:
            parent_up(callable): indicates if the upstream power is available
            power_up_on_charge(boolean): indicates if the asset should be powered up when min charge level is achieved

        """

        battery_level = self.state.battery_level
        powered = False

        # keep charging battery while its level is less than max & parent is up
        while battery_level < self.state.battery_max_level and parent_up():

            # calculate new battery level
            battery_level = battery_level + (self._charge_per_second * self._charge_speed_factor)

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(self._cacl_time_left(self.state.wattage) * 60 * 100)

            # power up on min charge level
            if (not powered and power_up_on_charge) and (battery_level > self.state.min_restore_charge_level):
                e_result = self.power_up()
                powered = e_result.new_state
                self.state.publish_power()

            time.sleep(1)


    def _launch_battery_drain(self):
        """Start a thread that will decrease battery level """

        self._start_time_battery = dt.datetime.now()

        # update state details
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onBattery)
        self.state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.deepMomentarySag)
        
        # launch a thread
        self._battery_drain_t = Thread(
            target=self._drain_battery, 
            args=(lambda: self._parent_up,), 
            name="battery_drain:{}".format(self.key)
        )
        self._battery_drain_t.daemon = True
        self._battery_drain_t.start()


    def _launch_battery_charge(self, power_up_on_charge=False):
        """Start a thread that will charge battery level """
        self.state.update_time_on_battery(0)

        # update state details
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onLine)
        self.state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.noTransfer)

        # launch a thread
        self._battery_charge_t = Thread(
            target=self._charge_battery, 
            args=(lambda: self._parent_up, power_up_on_charge),
            name="battery_charge:{}".format(self.key)    
        )
        self._battery_charge_t.daemon = True
        self._battery_charge_t.start()


    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Upstream power was lost"""

        self._parent_up = False

        # If battery is still alive -> keep UPS up
        if self.state.battery_level:
            self._launch_battery_drain()
            event.success = False
            return

        # Battery is dead
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.off)

        e_result = self.power_off()
        event.success = e_result.new_state != e_result.old_state

        return e_result   
    
    @handler("SignalDown")
    def on_signal_down_received(self, event, *args, **kwargs):
        """UPS can be powered down by snmp command"""
        self.state.update_ups_output_status(sm.UPSStateManager.OutputStatus.off)

        if 'graceful' in kwargs and kwargs['graceful']:
            e_result = self.shut_down()
        else:
            e_result = self.power_off()
        
        event.success = e_result.new_state != e_result.old_state

        return e_result  

    @handler("ButtonPowerUpPressed")
    def on_ups_signal_up(self):
        if self._parent_up:
            self._launch_battery_charge()
        else:
            self._launch_battery_drain()


    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        
        self._parent_up = True
        battery_level = self.state.battery_level
        self._launch_battery_charge(power_up_on_charge=(not battery_level))

        if battery_level:
            e_result = self.power_up()
            event.success = e_result.new_state != e_result.old_state

            return e_result
        else:
            event.success = False
            return None
    

    @handler("AmbientDecreased", "AmbientIncreased")
    def on_ambient_updated(self):
        self._state.update_temperature(7)

    # @handler("AmbientIncreased")
    # def on_ambient_increased(self):
    #     self._state.update_temperature(7)


    @property
    def charge_speed_factor(self):
        """Estimated charge/sec will be multiplied by this value"""
        return self._charge_speed_factor

    @charge_speed_factor.setter 
    def charge_speed_factor(self, speed):
        self._charge_speed_factor = speed

    @property
    def drain_speed_factor(self):
        """Estimated drain/sec will be multiplied by this value"""        
        return self._drain_speed_factor

    @drain_speed_factor.setter 
    def drain_speed_factor(self, speed):
        self._drain_speed_factor = speed

    def _update_load(self, load_change, arithmetic_op, msg=''):
        upd_result = super()._update_load(load_change, arithmetic_op, msg)
        # re-calculate time left based on updated load
        self.state.update_time_left(self._cacl_time_left(self.state.wattage) * 60 * 100)
        return upd_result


@register_asset
class Outlet(Asset):

    channel = "engine-outlet"
    StateManagerCls = sm.OutletStateManager


    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))


    ##### React to any events of the connected components #####    

    @handler("SignalDown", priority=1)
    def on_signal_down_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state 
        (if if one is updated, other ones should be updated as well)"""
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOff)

    @handler("SignalUp", priority=1)
    def on_signal_up_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state"""     
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOn)
            

    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        """ React to events with power down """
        if 'delayed' in kwargs and kwargs['delayed']:
            time.sleep(self.state.get_config_off_delay())

        return self.power_off()

    @handler("ParentAssetPowerUp", "SignalUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """ React to events with power up """

        if 'delayed' in kwargs and kwargs['delayed']:
            time.sleep(self.state.get_config_on_delay())

        e_result = self.power_up()
        event.success = e_result.new_state != e_result.old_state

        return e_result
        

    @handler("SignalReboot")
    def on_reboot_request_received(self, event, *args, **kwargs):
        """Received reboot request"""
        old_state = self.state.status
        
        self.power_off()
        e_result_up = self.power_up()
        if not e_result_up.new_state:
            event.success = False

        return PowerEventResult(
            old_state=old_state,
            new_state=e_result_up.new_state,
            asset_key=self.state.key,
            asset_type=self.state.asset_type
        )


@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = sm.StaticDeviceStateManager
    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))
        self.state.update_load(self.state.power_usage)

    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs): 
        return self.power_off()


    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        return self.power_up()


@register_asset
class Server(StaticAsset):
    """Asset controlling a VM (without IPMI support) """
    channel = "engine-server"
    StateManagerCls = sm.ServerStateManager

    def __init__(self, asset_info):
        super(Server, self).__init__(asset_info)
        self.state.power_up()
    
    
@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI support """


    channel = "engine-bmc"
    StateManagerCls = sm.BMCServerStateManager
    
    def __init__(self, asset_info):

        # create state directory
        ipmi_dir = os.path.join(sm.StateManager.get_temp_workplace_dir(), str(asset_info['key']))
        sensors = self.StateManagerCls.get_sensor_definitions(asset_info['key'])
        os.makedirs(ipmi_dir)

        self._ipmi_agent = IPMIAgent(asset_info['key'], ipmi_dir, ipmi_config=asset_info, sensors=sensors)
        super(ServerWithBMC, self).__init__(asset_info)
       
        
    
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        self._ipmi_agent.stop_agent()
        return self.power_off()


    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        self._ipmi_agent.start_agent() 
        return self.power_up()


@register_asset
class PSU(StaticAsset):
    """PSU """


    channel = "engine-psu"
    StateManagerCls = sm.PSUStateManager

    def __init__(self, asset_info):
        if asset_info['variation'] == 'server':
            PSU.StateManagerCls = sm.SimplePSUStateManager
        self._var = asset_info['variation'] 
        super(PSU, self).__init__(asset_info)


    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        if self._var != 'server':
            self.state.set_psu_status(0x08)

    
    @handler("ButtonPowerUpPressed")
    def on_asset_did_power_on(self):
        if self._var != 'server':
            self.state.set_psu_status(0x01)
