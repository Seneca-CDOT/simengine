"""Access to outlet state"""
from enginecore.state.api.snmp_state import ISnmpDeviceStateManager

from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IOutletStateManager(ISnmpDeviceStateManager):
    """Exposes state logic for Outlet asset """
