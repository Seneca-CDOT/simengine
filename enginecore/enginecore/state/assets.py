""" This file contains definitions of Asset classes """
import subprocess
import os
import signal

from circuits import Component, handler
from enginecore.state.state_managers import PDUStateManager, OutletStateManager

SUPPORTED_ASSETS = {}


class Asset(Component):
    def __init__(self, key):
        super(Asset, self).__init__()
        self._key = key

    def get_key(self):
        return self._key


def register_asset(cls):
    """
    This decorator maps string class names to classes
    (It is basically a factory)
    """
    SUPPORTED_ASSETS[cls.__name__.lower()] = cls
    return cls


class SNMPAgent():
    
    agent_num = 1
    def __init__(self, key):

        self._key_space_id = key
        self._process = None
        self.start_agent()
       
        SNMPAgent.agent_num += 1


    def stop_agent(self):
        os.kill(self._process.pid, signal.SIGSTOP)


    def start_agent(self):
        
        # resume if process has been paused
        if self._process:
            os.kill(self._process.pid, signal.SIGCONT)
            return

        # start a new one
        cmd = "snmpsimd.py --agent-udpv4-endpoint=127.0.0.{}:1024".format(SNMPAgent.agent_num)
        cmd += " --variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id)
        self._process = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=open(os.devnull, 'wb'), close_fds=True)
        print ("Started SNMPsim process under pid {}".format(self._process.pid))
    

@register_asset
class PDU(Asset):

    channel = "pdu"
    StateManagerCls = PDUStateManager

    def __init__(self, key):
        super(PDU, self).__init__(key)

        self._pdu_state = PDU.StateManagerCls(key)
        self._snmp_agent = SNMPAgent(key)


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


    def __init__(self, key):
        super(Outlet, self).__init__(key)
        self._outlet_state = Outlet.StateManagerCls(key)


    ##### React to any events of the connected components #####    
    @handler("PDUPowerDown")
    def power_down(self): 
        self._outlet_state.power_down()


    @handler("PDUPowerUp")
    def power_up(self):
        self._outlet_state.power_up()


