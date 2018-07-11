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
from distutils.dir_util import copy_tree
from string import Template

from circuits import Component, handler
import enginecore.state.state_managers as sm

SUPPORTED_ASSETS = {}

def register_asset(cls):
    """
    This decorator maps string class names to classes
    (It is basically a factory)
    """
    SUPPORTED_ASSETS[cls.__name__.lower()] = cls
    return cls


class Asset(Component):
    """ Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self._state.reset_boot_time()
        self._state.update_load(0)

    def get_key(self):
        """ Get ID assigned to the asset """
        return self._state.get_key()

    def get_load(self):
        return self._state.get_load()
    
    def get_amperage(self):
        return self._state.get_amperage()

    def status(self):
        """ Get Asset status stored in redis db """
        return self._state.status()

    def power_up(self):
        """ Power up this asset """
        return self._state.get_key(), self._state.get_type(), self._state.power_up()

    def power_off(self):
        """ Power down this asset """
        return self._state.get_key(), self._state.get_type(), self._state.power_off()

    ##### React to events associated with the asset #####
    def on_asset_power_down(self):
        """ Call when state of an asset is switched to 'off' """
        raise NotImplementedError

    def on_asset_power_up(self):
        """ Call when state of an asset is switched to 'on' """
        raise NotImplementedError


    ##### React to any events of the connected components #####
    def on_parent_power_down(self):
        """ Upstream loss of power """
        raise NotImplementedError

    def on_parent_power_up(self):
        """ Upstream power restored """        
        raise NotImplementedError

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased")
    def on_load_increase(self, event, *args, **kwargs):
        increased_by = kwargs['child_load']
        old_load = self._state.get_load()
        # print('Asset : {} : orig load {}, increased by: {}'.format(self._state.get_key(), old_load, increased_by))
        self._state.update_load(old_load + increased_by)
        return increased_by, self._state.get_key()

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased")
    def on_load_decrease(self, event, *args, **kwargs):
        decreased_by = kwargs['child_load']
        old_load = self._state.get_load()
        # print('Asset : {} : orig load {}, decreased by: {}'.format(self._state.get_key(), old_load, decreased_by))
        self._state.update_load(old_load - decreased_by)
        return decreased_by, self._state.get_key()


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
    def __init__(self, key, ipmi_dir):
        super(IPMIAgent, self).__init__()
        self._asset_key = key
        self._process = None
        self._ipmi_dir = ipmi_dir
        copy_tree(os.environ.get('SIMENGINE_IPMI_TEMPL'), self._ipmi_dir)
        
        # Substitute a template
        lan_conf = os.path.join(self._ipmi_dir, 'lan.conf')
        ipmisim_emu = os.path.join(self._ipmi_dir, 'ipmisim1.emu')

        lan_conf_opt = {'asset_key': key, 'extend_lib': '/home/huanshi/dev/simengine/enginecore/ipmi_sim/haos_extend.so'}
        ipmisim_emu_opt = {'ipmi_dir': self._ipmi_dir}

        with open(lan_conf, "r+") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(lan_conf_opt))

        with open(ipmisim_emu, "r+") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(ipmisim_emu_opt))


        print(self._ipmi_dir)

        self.start_agent()
        IPMIAgent.agent_num += 1
    
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

    def __init__(self, key, community='public', lookup_oid='1.3.6', host=False):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key
        self._process = None
        self._snmp_rec_filename = community + '.snmprec'
        self._snmp_rec_dir = tempfile.mkdtemp()
        self._host = host if host else "127.0.0.{}:1024".format(SNMPAgent.agent_num)

        snmp_rec_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_filename)
        redis_script_sha = os.environ.get('SIMENGINE_SNMP_SHA')

        with open(snmp_rec_filepath, "a") as tmp:
            tmp.write("{}|:redis|key-spaces-id={},evalsha={}\n".format(lookup_oid, key, redis_script_sha))
            
        self.start_agent()

        SNMPAgent.agent_num += 1


    def stop_agent(self):
        """ Logic for agent's termination """
        os.kill(self._process.pid, signal.SIGSTOP)


    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(os.path.join(self._snmp_rec_dir, self._snmp_rec_filename))


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
    

@register_asset
class PDU(Asset):

    channel = "engine-pdu"
    StateManagerCls = sm.PDUStateManager

    def __init__(self, asset_info):
        super(PDU, self).__init__(PDU.StateManagerCls(asset_info))

        self._snmp_agent = SNMPAgent(
            asset_info['key'],
            host=asset_info['host'] if 'host' in asset_info else False
        )


    ##### Create/kill SNMP agent when PDU state changes
    @handler("AssetPowerDown")
    def on_asset_power_down(self):
        self._snmp_agent.stop_agent()


    @handler("AssetPowerUp")
    def on_asset_power_up(self):
        self._snmp_agent.start_agent()

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_power_down(self): 
        return self.power_off()

    @handler("ParentAssetPowerUp")
    def on_parent_power_up(self):
        return self.power_up()



@register_asset
class Outlet(Asset):

    channel = "engine-outlet"
    StateManagerCls = sm.OutletStateManager


    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))


    ##### React to any events of the connected components #####    
    @handler("ParentAssetPowerDown", "SignalDown")
    def on_parent_power_down(self):
        """ React to events with power down """
        return self.power_off()


    @handler("ParentAssetPowerUp", "SignalUp")
    def on_parent_power_up(self):
        """ React to events with power up """
        return self.power_up()


@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = sm.StaticDeviceStateManager
    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))
        self._state.update_load(self._state.get_amperage())

    @handler("ParentAssetPowerDown")
    def on_parent_power_down(self): 
        return self.power_off()


    @handler("ParentAssetPowerUp")
    def on_parent_power_up(self):
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
        super(ServerWithBMC, self).__init__(asset_info)
        self._ipmi_agent = IPMIAgent(asset_info['key'], asset_info['ipmi_dir'])
        

@register_asset
class PSU(StaticAsset):
    """PSU """
    channel = "engine-psu"
    StateManagerCls = sm.PSUStateManager

    def __init__(self, asset_info):
        super(PSU, self).__init__(asset_info)