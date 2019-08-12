"""Aggregates event-handling logic for devices supporting SNMP interface"""

from circuits import handler
from enginecore.state.agent import SNMPAgent


class SNMPSim:
    """Snmp simulator running snmpsim program"""

    def __init__(self, key, host, port):
        self._snmp_agent = SNMPAgent(key, host, port)

    @handler("ButtonPowerDownPressed")
    def on_asset_did_power_off(self):
        """Stop snmpsim program when power down button is pressed
        (note that this doesn't handle ParentPowerDown since some 
        SNMP devices don't power down on upstream power loss)
        """
        self._snmp_agent.stop_agent()

    @handler("ButtonPowerUpPressed", "ParentAssetPowerUp")
    def on_asset_did_power_on(self):
        """Restart agent when upstream power is restored"""
        self._snmp_agent.start_agent()
