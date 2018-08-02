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
import signal
import tempfile
import shutil
import time
from threading import Thread
from collections import namedtuple
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

        # Template options
        lan_conf_opt = {
            'asset_key': key, 
            'extend_lib': '/usr/lib64/simengine/haos_extend.so',
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

        self.start_agent()
        IPMIAgent.agent_num += 1

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

        cmd = "ipmi_sim -c {} -f {} -s {} -n".format(lan_conf, ipmisim_emu, state_dir)
        print(cmd)
        self._process = subprocess.Popen(
            cmd, shell=True, stderr=subprocess.DEVNULL, stdout=open(os.devnull, 'wb'), close_fds=True
        )

        print("Started ipmi_sim process under pid {}".format(self._process.pid))


    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_agent()

class SNMPAgent(Agent):
    """ SNMP simulator instance """

    def __init__(self, key, public_community='public', private_community='private', lookup_oid='1.3.6', host=False):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key
        self._process = None
        self._snmp_rec_public_fname = public_community + '.snmprec'
        self._snmp_rec_private_fname = private_community + '.snmprec'

        self._snmp_rec_dir = tempfile.mkdtemp()
        self._host = '{}:1024'.format(host) if host else "127.0.0.{}:1024".format(SNMPAgent.agent_num)

        snmp_rec_public_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_public_fname)
        snmp_rec_private_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_private_fname)

        redis_script_sha = os.environ.get('SIMENGINE_SNMP_SHA')
        snmpsim_config = "{}|:redis|key-spaces-id={},evalsha={}\n".format(lookup_oid, key, redis_script_sha)

        with open(snmp_rec_public_filepath, "a") as tmp_pub, open(snmp_rec_private_filepath, "a") as tmp_priv:
            tmp_pub.write(snmpsim_config)
            tmp_priv.write(snmpsim_config)
            
        self.start_agent()

        SNMPAgent.agent_num += 1


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
        cmd = "snmpsimd.py --agent-udpv4-endpoint={}".format(self._host)
        cmd += " --variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id)
        cmd += " --data-dir="+self._snmp_rec_dir
        cmd += " --transport-id-offset="+str(SNMPAgent.agent_num)
        
        self._process = subprocess.Popen(
            cmd, shell=True, stderr=subprocess.DEVNULL, stdout=open(os.devnull, 'wb'), close_fds=True
        )

        print("Started SNMPsim process under pid {}".format(self._process.pid))


class SNMPSim():
    
    def __init__(self, key, host=False):
        self._snmp_agent = SNMPAgent(
            key,
            host=host
        )


    ##### Create/kill SNMP agent when state changes
    @handler("AssetPowerDown")
    def on_asset_did_power_off(self):
        self._snmp_agent.stop_agent()


    @handler("AssetPowerUp", "ParentAssetPowerUp")
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
            host=asset_info['host'] if 'host' in asset_info else False
        )

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_power_off_request_received(self):
        return self.power_off()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        return self.power_up()


@register_asset
class UPS(Asset, SNMPSim):
    channel = "engine-ups"
    StateManagerCls = sm.UPSStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, UPS.StateManagerCls(asset_info))
        SNMPSim.__init__(
            self, 
            key=asset_info['key'],
            host=asset_info['host'] if 'host' in asset_info else False
        )

        # Threads responsible for battery charge/discharge

        self._parent_up = True
        self._battery_drain_t = None
        self._battery_charge_t = None

        self._state.update_battery(self._state.battery_max_level)
        self._battery_discharge = 100


    def _drain_battery(self, parent_up):
        
        battery_level = self._state.battery_level
        # drain power
        while battery_level > 0 and self._state.status and not parent_up():
            battery_level = battery_level - self._battery_discharge
            self._state.update_battery(battery_level)
            time.sleep(1)
        
        # power off if still alive
        if self._state.status and not parent_up():
            self._state.power_off()
            self._state.publish_power()


    def _charge_battery(self, parent_up):
        
        battery_level = self._state.battery_level

        # charge -> (only if the upstream power is available (the battery is not being drained))
        while battery_level != self._state.battery_max_level and parent_up():
            battery_level = battery_level + self._battery_discharge
            self._state.update_battery(battery_level)
            time.sleep(1)

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):

        self._parent_up = False

        if self._state.battery_level:
            self._battery_drain_t = Thread(target=self._drain_battery, args=(lambda: self._parent_up,))
            self._battery_drain_t.start()

            event.success = False
            return

        if 'graceful' in kwargs and kwargs['graceful']:
            return self.shut_down()

        return self.power_off()
    
    @handler("AssetPowerUp")
    def on_ups_signal_up(self):
        print(self._parent_up)
        if self._parent_up:
            self._battery_charge_t = Thread(target=self._charge_battery,  args=(lambda: self._parent_up,))
            self._battery_charge_t.start()
        else:
            self._battery_drain_t = Thread(target=self._drain_battery, args=(lambda: self._parent_up,))
            self._battery_drain_t.start()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):

        self._parent_up = True

        self._battery_charge_t = Thread(target=self._charge_battery,  args=(lambda: self._parent_up,))
        self._battery_charge_t.start()
        return self.power_up()

@register_asset
class Outlet(Asset):

    channel = "engine-outlet"
    StateManagerCls = sm.OutletStateManager


    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))


    ##### React to any events of the connected components #####    
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
        asset_info['ipmi_dir'] = tempfile.mkdtemp()
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
        super(PSU, self).__init__(asset_info)

    @handler("AssetPowerDown")
    def on_asset_did_power_off(self):
        self._state.set_psu_status(0x08)

    
    @handler("AssetPowerUp")
    def on_asset_did_power_on(self):
        self._state.set_psu_status(0x01)