"""This file contains definitions of Assets 

Each asset class contains reactive logic associated with certain events. 

Example:
    a PDU asset will be instantiated if there's a node labeled as "PDU" in a graph db (:PDU),
    isntance of a PDU asset can react to upstream power loss or any other event defined 
    as a handler.
    It can also wrap SNMPAgent if supported.

"""
import subprocess
import os
import pwd
import grp
import signal
import tempfile
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

class Asset(Component):
    """ Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self._state.reset_boot_time()
        self._state.update_load(0)

    @property
    def key(self):
        """ Get ID assigned to the asset """
        return self._state.key

    @property
    def state(self):
        """State manager instance"""
        return self._state
    
    def power_up(self):
        """ Power up this asset """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self._state.key, 
            asset_type=self._state.asset_type, 
            old_state=old_state,
            new_state=self._state.power_up()
        )

    def shut_down(self):
        """ Shut down this asset """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self._state.key, 
            asset_type=self._state.asset_type, 
            old_state=old_state,
            new_state=self._state.shut_down()
        )

    def power_off(self):
        """ Power down this asset """
        old_state = self.state.status
        return PowerEventResult(
            asset_key=self._state.key, 
            asset_type=self._state.asset_type, 
            old_state=old_state,
            new_state=self._state.power_off()
        )

    def _update_load(self, load_change, op, msg=''):
        """React to load changes by updating asset load
        
        Args:
            load_change(float): how much AMPs need to be added/subtracted
            op(callable): calculates new load (receives old load & measured load change)
            msg(str): message to be printed
        
        Returns:
            LoadEventResult: Event result containing old & new load values as well as value subtracted/added
        """
        
        old_load = self._state.load
        new_load = op(old_load, load_change)
        
        if msg:
            print(msg.format(self._state.key, old_load, load_change, new_load))
        
        self.state.update_load(new_load)

        return LoadEventResult(
            load_change=load_change,
            old_load=old_load,
            new_load=new_load,
            asset_key=self._state.key
        )

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased")
    def on_load_increase(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased"""
        increased_by = kwargs['child_load']
        msg = 'Asset : {} : orig load {}, increased by: {}, new load: {}'
        return self._update_load(increased_by, lambda old, change: old+change, msg)

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased"""
        decreased_by = kwargs['child_load']
        msg = 'Asset : {} : orig load {}, decreased by: {}, new load: {}'
        return self._update_load(decreased_by, lambda old, change: old-change, msg)

    ##### React to events associated with the asset #####
    def on_asset_did_power_off(self):
        """ Call when state of an asset is switched to 'off' """
        raise NotImplementedError

    def on_asset_did_power_on(self):
        """ Call when state of an asset is switched to 'on' """
        raise NotImplementedError


    ##### React to any events of the connected components #####
    def on_power_off_request_received(self):
        """ Upstream loss of power """
        raise NotImplementedError

    def on_power_up_request_received(self):
        """ Upstream power restored """        
        raise NotImplementedError

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS

    @classmethod
    def get_state_manager_by_key(cls, key, notify=True):
        return sm.StateManager.get_state_manager_by_key(key, cls.get_supported_assets(), notify)

class Agent():
    """ Abstract Agent Class """
    agent_num = 1    
    
    def start_agent(self):
        """ Logic for starting up the agent """
        raise NotImplementedError

    def stop_agent(self):
        """ Logic for agent's termination """
        raise NotImplementedError
    

class IPMIAgent(Agent):
    """IPMIsim instance """
    def __init__(self, key, ipmi_dir, num_psu, host='localhost', port=9001, vmport=9002, user='ipmiusr', password='test'):
        super(IPMIAgent, self).__init__()
        self._asset_key = key
        self._process = None
        self._ipmi_dir = ipmi_dir
        copy_tree(os.environ.get('SIMENGINE_IPMI_TEMPL'), self._ipmi_dir)

        # sensor, emu & lan configuration file paths
        lan_conf = os.path.join(self._ipmi_dir, 'lan.conf')
        ipmisim_emu = os.path.join(self._ipmi_dir, 'ipmisim1.emu')
        sdr_main = os.path.join(*[self._ipmi_dir, 'emu_state', 'ipmi_sim', 'ipmisim1', 'sdr.20.main'])
        sensor_def = os.path.join(self._ipmi_dir, 'main.sdrs')

        lib_path = os.path.join(sysconfig.get_config_var('LIBDIR'), "simengine", 'haos_extend.so')

        # Template options
        lan_conf_opt = {
            'asset_key': key, 
            'extend_lib': lib_path,
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'vmport': vmport
        }
        ipmisim_emu_opt = {'ipmi_dir': self._ipmi_dir, 'includes': ''}
        main_sdr_opt = {'ipmi_dir': self._ipmi_dir, 'includes': ''}

        # Set server-specific includes
        if num_psu == 2:
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
    
    @property
    def pid(self):
        return self._process.pid

    def _substitute_template_file(self, filename, options):
        """Update file using python templating """
        with open(filename, "r+") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(options))

    def stop_agent(self):
        """ Logic for agent's termination """
        os.kill(self._process.pid, signal.SIGSTOP)

    def start_agent(self):
        """ Logic for starting up the agent """
        # resume if process has been paused
        if self._process:
            os.kill(self._process.pid, signal.SIGCONT)
            return

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

        self._process = subprocess.Popen(
            cmd, stderr=subprocess.DEVNULL, close_fds=True
        )

        print("Started ipmi_sim process under pid {}".format(self._process.pid))

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_agent()

class SNMPAgent(Agent):
    """ SNMP simulator instance """

    def __init__(self, key, host, port, public_community='public', private_community='private', lookup_oid='1.3.6'):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key
        self._process = None
        self._snmp_rec_public_fname = public_community + '.snmprec'
        self._snmp_rec_private_fname = private_community + '.snmprec'

        sys_temp = tempfile.gettempdir()
        simengine_temp = os.path.join(sys_temp, 'simengine')
        
        self._snmp_rec_dir = os.path.join(simengine_temp, str(key))
        os.makedirs(self._snmp_rec_dir)
        self._host = '{}:{}'.format(host, port)
        
        uid = pwd.getpwnam("nobody").pw_uid
        gid = grp.getgrnam("nobody").gr_gid
        
        os.chown(self._snmp_rec_dir, uid, gid)
        snmp_rec_public_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_public_fname)
        snmp_rec_private_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_private_fname)

        redis_script_sha = os.environ.get('SIMENGINE_SNMP_SHA')
        snmpsim_config = "{}|:redis|key-spaces-id={},evalsha={}\n".format(lookup_oid, key, redis_script_sha)

        with open(snmp_rec_public_filepath, "a") as tmp_pub, open(snmp_rec_private_filepath, "a") as tmp_priv:
            tmp_pub.write(snmpsim_config)
            tmp_priv.write(snmpsim_config)
            
        self.start_agent()

        SNMPAgent.agent_num += 1


    @property
    def pid(self):
        return self._process.pid
        
    def stop_agent(self):
        """ Logic for agent's termination """
        os.kill(self._process.pid, signal.SIGSTOP)


    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(os.path.join(self._snmp_rec_dir, self._snmp_rec_public_fname))


    def start_agent(self):
        """ Logic for starting up the agent """
        # resume if process has been paused
        if self._process:
            os.kill(self._process.pid, signal.SIGCONT)
            return

        # start a new one
        cmd = ["snmpsimd.py", 
               "--agent-udpv4-endpoint={}".format(self._host),
               "--variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id),
               "--data-dir="+self._snmp_rec_dir,
               "--transport-id-offset="+str(SNMPAgent.agent_num),
               "--process-user=nobody",
               "--process-group=nobody"
              ]

        print(' '.join(cmd))
        self._process = subprocess.Popen(
            cmd, stderr=subprocess.DEVNULL, close_fds=True
        )
    
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

    channel = "engine-pdu"
    StateManagerCls = sm.PDUStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, PDU.StateManagerCls(asset_info))
        SNMPSim.__init__(
            self, 
            key=asset_info['key'],
            host=asset_info['host'] if 'host' in asset_info else 'localhost',
            port=asset_info['port'] if 'port' in asset_info else 161
        )

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        
        e_result = self.power_off()
        
        if e_result.new_state == e_result.old_state:
            event.success = False

        return e_result

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        e_result = self.power_up()

        if e_result.new_state == e_result.old_state:
            event.success = False

        return e_result


@register_asset
class UPS(Asset, SNMPSim):
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
        self._state.update_battery(self._state.battery_max_level)
        
        # get charge per second using full recharge time (hrs)
        self._charge_per_second = self._state.battery_max_level / (self._state.full_recharge_time*60*60)


    def _cacl_time_left(self, wattage):
        """Approximate runtime estimation based on current battery level""" 
        return (self._calc_full_power_time_left(wattage)*self._state.battery_level)/self._state.battery_max_level

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
        # Get the wattage 
        wattage = self._state.wattage
        fp_estimated_timeleft = self._calc_full_power_time_left(wattage)
        return self._state.battery_max_level / (fp_estimated_timeleft*60)


    def _drain_battery(self, parent_up):
        """When parent is not available -> drain battery """

        battery_level = self._state.battery_level
        blackout = False

        # drain power
        while battery_level > 0 and self._state.status and not parent_up():
            battery_level = battery_level - (self._calc_battery_discharge() * self._drain_speed_factor)
            seconds_on_battery = (dt.datetime.now() - self._start_time_battery).seconds
            self._state.update_battery(battery_level)
            self._state.update_time_left(self._cacl_time_left(self._state.wattage) * 60 * 100)
            self._state.update_time_on_battery(seconds_on_battery * 100)
            
            if seconds_on_battery > 5 and not blackout:
                blackout = True
                self._state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.blackout)
            
            time.sleep(1)
        
        # kill the thing if still breathing
        if self._state.status and not parent_up():
            self._snmp_agent.stop_agent()
            self._state.power_off()
            self._state.publish_power()


    def _charge_battery(self, parent_up, power_up_on_charge=False):
        """Charge battery when there's upstream power source & battery is not full"""

        battery_level = self._state.battery_level
        powered = False

        # charge -> (only if the upstream power is available (the battery is not being drained))
        while battery_level < self._state.battery_max_level and parent_up():
            battery_level = battery_level + (self._charge_per_second * self._charge_speed_factor)
            self._state.update_battery(battery_level)
            self._state.update_time_left(self._cacl_time_left(self._state.wattage) * 60 * 100)
            if (not powered and power_up_on_charge) and (battery_level > self._state.min_restore_charge_level):
                e_result = self.power_up()
                powered = e_result.new_state
                self._state.publish_power()

            time.sleep(1)

    def _launch_battery_drain(self):
        """Start a thread that will decrease battery level """
        self._start_time_battery = dt.datetime.now()

        self._state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onBattery)
        self._state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.deepMomentarySag)
        
        self._battery_drain_t = Thread(
            target=self._drain_battery, 
            args=(lambda: self._parent_up,), 
            name="battery_drain:{}".format(self.key)
        )
        self._battery_drain_t.daemon = True
        self._battery_drain_t.start()

    def _launch_battery_charge(self, power_up_on_charge=False):
        """Start a thread that will charge battery level """
        self._state.update_time_on_battery(0)

        self._state.update_ups_output_status(sm.UPSStateManager.OutputStatus.onLine)
        self._state.update_transfer_reason(sm.UPSStateManager.InputLineFailCause.noTransfer)

        self._battery_charge_t = Thread(
            target=self._charge_battery, 
            args=(lambda: self._parent_up, power_up_on_charge),
            name="battery_charge:{}".format(self.key)    
        )
        self._battery_charge_t.daemon = True
        self._battery_charge_t.start()


    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        
        self._parent_up = False

        # If battery is still alive -> keep UPS up
        if self._state.battery_level:
            self._launch_battery_drain()
            event.success = False
            return

        # Battery is dead
        self._state.update_ups_output_status(sm.UPSStateManager.OutputStatus.off)

        if 'graceful' in kwargs and kwargs['graceful']:
            e_result = self.shut_down()
        else:
            e_result = self.power_off()
        
        if e_result.new_state == e_result.old_state:
            event.success = False

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
        battery_level = self._state.battery_level
        self._launch_battery_charge(power_up_on_charge=(not battery_level))

        if battery_level:
            e_result = self.power_up()
            if e_result.new_state == e_result.old_state:
                event.success = False

            return e_result
        else:
            event.success = False
            return None
    
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

    def _update_load(self, load_change, op, msg=''):
        upd_result = super()._update_load(load_change, op, msg)
        self._state.update_time_left(self._cacl_time_left(self._state.wattage) * 60 * 100)
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
        self._state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOff)

    @handler("SignalUp", priority=1)
    def on_signal_up_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state"""     
        self._state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOn)
            

    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        """ React to events with power down """
        if 'delayed' in kwargs and kwargs['delayed']:
            time.sleep(self._state.get_config_off_delay())

        return self.power_off()

    @handler("ParentAssetPowerUp", "SignalUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """ React to events with power up """

        if 'delayed' in kwargs and kwargs['delayed']:
            time.sleep(self._state.get_config_on_delay())

        e_result = self.power_up()

        if e_result.new_state == e_result.old_state:
            event.success = False

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
            asset_key=self._state.key,
            asset_type=self._state.asset_type
        )

@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = sm.StaticDeviceStateManager
    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))
        self._state.update_load(self._state.power_usage)

    @handler("ParentAssetPowerDown")
    def on_power_off_request_received(self, event, *args, **kwargs): 
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
        self._state.power_up()
    
@register_asset
class ServerWithBMC(Server):
    """Asset controlling a VM with BMC/IPMI support """
    channel = "engine-bmc"
    StateManagerCls = sm.BMCServerStateManager
    
    def __init__(self, asset_info):

        sys_temp = tempfile.gettempdir()
        simengine_temp = os.path.join(sys_temp, 'simengine')
        
        asset_info['ipmi_dir'] = os.path.join(simengine_temp, str(asset_info['key']))
        os.makedirs(asset_info['ipmi_dir'])
        
        self._ipmi_agent = IPMIAgent(
            asset_info['key'], 
            asset_info['ipmi_dir'], 
            num_psu=asset_info['num_components'],
            host=asset_info['host'],
            user=asset_info['user'],
            password=asset_info['password'],
            port=asset_info['port'],
            vmport=asset_info['vmport']
        )

        super(ServerWithBMC, self).__init__(asset_info)
        self._state.set_state_dir(asset_info['ipmi_dir'])

        
    
    @handler("ParentAssetPowerDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
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
            self._state.set_psu_status(0x08)

    
    @handler("ButtonPowerUpPressed")
    def on_asset_did_power_on(self):
        if self._var != 'server':
            self._state.set_psu_status(0x01)
