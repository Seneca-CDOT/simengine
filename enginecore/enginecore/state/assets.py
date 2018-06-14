""" This file contains definitions of Assets 

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

from circuits import Component, handler
from enginecore.state.state_managers import PDUStateManager, OutletStateManager

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

    def __init__(self, asset_info):
        super(Asset, self).__init__()
        self._asset_info = asset_info

    def get_key(self):
        """ Get ID assigned to the asset """
        return self._asset_info['key']


    ##### React to events associated with the asset #####
    def on_asset_power_down(self):
        """ Call when state of an asset is switched to 'off' """
        raise NotImplementedError

    def on_asset_power_up(self):
        """ Call when state of an asset is switched to 'on' """
        raise NotImplementedError


    ##### React to any events of the connected components #####
    def power_down(self):
        """ Upstream loss of power """
        raise NotImplementedError

    def power_up(self):
        """ Upstream power restored """        
        raise NotImplementedError


class Agent():
    """ Abstract Agent Class """
    
    def start_agent(self):
        """ Logic for starting up the agent """
        raise NotImplementedError

    def stop_agent(self):
        """ Logic for agent's termination """
        raise NotImplementedError
    


class SNMPAgent(Agent):
    """ SNMP simulator instance """

    agent_num = 1
    def __init__(self, key, community='public', lookup_oid='1.3.6'):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key
        self._process = None
        self._snmp_rec_filename = community + '.snmprec'
        self._snmp_rec_dir = tempfile.mkdtemp()

        snmp_rec_filepath = os.path.join(self._snmp_rec_dir, self._snmp_rec_filename)

        with open(snmp_rec_filepath, "a") as tmp:
            tmp.write("{}|:redis|key-spaces-id={}\n".format(lookup_oid, key))
            
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
        cmd = "snmpsimd.py --agent-udpv4-endpoint=127.0.0.{}:1024".format(SNMPAgent.agent_num)
        cmd += " --variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id)
        cmd += " --data-dir="+self._snmp_rec_dir
        cmd += " --transport-id-offset="+str(SNMPAgent.agent_num)

        self._process = subprocess.Popen(
            cmd, shell=True, stderr=subprocess.DEVNULL, stdout=open(os.devnull, 'wb'), close_fds=True
        )

        print("Started SNMPsim process under pid {}".format(self._process.pid))
    

@register_asset
class PDU(Asset):

    channel = "pdu"
    StateManagerCls = PDUStateManager

    def __init__(self, asset_info):
        super(PDU, self).__init__(asset_info)

        self._pdu_state = PDU.StateManagerCls(asset_info['key'])
        self._snmp_agent = SNMPAgent(
            asset_info['key'],
        )


    ##### Create/kill SNMP agent when PDU state changes
    @handler("PDUPowerDown")
    def on_asset_power_down(self):
        self._snmp_agent.stop_agent()


    @handler("PDUPowerUp")
    def on_asset_power_up(self):
        self._snmp_agent.start_agent()


    ##### React to any events of the connected components #####
    @handler("OutletPowerDown")
    def power_down(self): 
        self._pdu_state.power_down()


    @handler("OutletPowerUp")
    def power_up(self):
        self._pdu_state.power_up()


@register_asset
class Outlet(Asset):

    channel = "outlet"
    StateManagerCls = OutletStateManager


    def __init__(self, asset_info):
        super(Outlet, self).__init__(asset_info)
        self._outlet_state = Outlet.StateManagerCls(asset_info['key'])


    ##### React to any events of the connected components #####    
    @handler("PDUPowerDown", "SignalDown")
    def power_down(self):
        """ React to events with power down """
        self._outlet_state.power_down()


    @handler("PDUPowerUp", "SignalUp")
    def power_up(self):
        """ React to events with power up """
        self._outlet_state.power_up()

