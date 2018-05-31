""" This file contains definitions of Asset classes """
import subprocess
import os

from circuits import Component, handler
import redis
from enginecore.state.state_managers import PDUStateManager, OutletStateManager

SUPPORTED_ASSETS = {}

def register_asset(cls):
    """
    This decorator maps string class names to classes
    (It is basically a factory)
    """
    SUPPORTED_ASSETS[cls.__name__.lower()] = cls
    return cls


# TODO: Agents do not exit gracefully
class SNMPAgent():
    
    agent_num = 1
    def __init__(self, key):

        self._key_space_id = key
        self.start_agent()
       
        SNMPAgent.agent_num += 1

    def kill_agent(self):
        self._process.kill()

    def start_agent(self):
        cmd = ["snmpsimd.py --agent-udpv4-endpoint=127.0.0.{}:1024".format(SNMPAgent.agent_num),
               "--variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"+str(self._key_space_id)]
        self._process = subprocess.Popen(cmd, shell=True, stderr=subprocess.DEVNULL,stdout=open(os.devnull, 'wb'), close_fds=True)
        print (self._process.pid)
        

@register_asset
class PDU(PDUStateManager):
    channel = "pdu"

    def __init__(self, key):
        super(PDUStateManager, self).__init__(key)
        self._snmp_agent = SNMPAgent(key)

    ##### Create/kill SNMP agent when PDU state changes
    @handler("PDUPowerDown")
    def on_asset_power_down(self):
        self._snmp_agent.kill_agent()

    @handler("PDUPowerUp")
    def on_asset_power_up(self):
        self._snmp_agent.start_agent()

    ##### React to any events of the connected components #####
    @handler("OutletPowerDown")
    def power_down(self): 
        super().power_down()

    @handler("OutletPowerUp")
    def power_up(self):
        super().power_up()


@register_asset
class Outlet(OutletStateManager):
    channel = "outlet"

    def __init__(self, key):
        super(OutletStateManager, self).__init__(key)

    ##### React to any events of the connected components #####    
    @handler("PDUPowerDown")
    def power_down(self): 
        super().power_down()

    @handler("PDUPowerUp")
    def power_up(self):
        super().power_up()


