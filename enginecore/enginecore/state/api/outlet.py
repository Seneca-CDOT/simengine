from enginecore.state.api.state import IStateManager

from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IOutletStateManager(IStateManager):
    """Exposes state logic for Outlet asset """
