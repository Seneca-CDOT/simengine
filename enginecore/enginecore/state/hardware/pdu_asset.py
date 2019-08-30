"""Event handler for PDU;
PDU is a rather dumb device, its power state changes
depending on the upstream power (parent)
Plus there's an SNMP agent running in the background
"""
# **due to circuit callback signature
# pylint: disable=W0613

import enginecore.state.hardware.internal_state as in_state
from enginecore.state.hardware.asset import Asset
from enginecore.state.hardware.snmp_asset import SNMPSim

from enginecore.state.hardware.asset_definition import register_asset


@register_asset
class PDU(Asset, SNMPSim):
    """Provides reactive logic for PDU & manages snmp simulator instance
    Example:
        powers down when upstream power becomes unavailable (and SNMP agent is unreachable)
        powers back up when upstream power is restored
    """

    channel = "engine-pdu"
    StateManagerCls = in_state.PDUStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, state=PDU.StateManagerCls(asset_info))
        SNMPSim.__init__(self, self._state)

    def power_up(self, state_reason=None):
        """Power up this asset 
        Returns: 
            int: new state after power_up operation
        """

        powered = super().power_up(state_reason)
        if powered:
            self._snmp_agent.start_agent()
            self._state.update_agent(self._snmp_agent.pid)

        return powered

    def power_off(self, state_reason=None):
        """Power down this asset 
        Returns: 
            int: new state after power_up operation
        """
        powered = super().power_off(state_reason)
        if not powered:
            self._snmp_agent.stop_agent()

        return powered

    def stop(self, code=None):
        self._snmp_agent.stop_agent()
        super().stop(code)
