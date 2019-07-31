"""Aggregates event-handling logic for devices supporting SNMP interface"""

import logging

from circuits import handler
from enginecore.state.agent import SNMPAgent

logger = logging.getLogger(__name__)


class SNMPSim:
    """Snmp simulator running snmpsim program"""

    def __init__(self, state):
        self._snmp_agent = SNMPAgent(state.key, state.snmp_config)

        self._state = state
        self._state.update_agent(self._snmp_agent.pid)

        logger.info(self._snmp_agent)

    @handler("PowerButtonOffEvent")
    def on_asset_did_power_off(self, event, *args, **kwargs):
        """Stop snmpsim program when power down button is pressed
        (note that this doesn't handle ParentPowerDown since some 
        SNMP devices don't power down on upstream power loss)
        """
        self._snmp_agent.stop_agent()

    @handler("PowerButtonOnEvent")
    def on_asset_did_power_on(self, event, *args, **kwargs):
        """Restart agent when upstream power is restored"""
        self._snmp_agent.start_agent()
        self._state.update_agent(self._snmp_agent.pid)
