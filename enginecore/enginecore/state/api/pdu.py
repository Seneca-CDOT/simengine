"""Access to PDU state details"""

from enginecore.tools.randomizer import Randomizer
from enginecore.state.api.snmp_state import ISnmpDeviceStateManager


@Randomizer.register
class IPDUStateManager(ISnmpDeviceStateManager):
    """Handles state logic for PDU asset """
