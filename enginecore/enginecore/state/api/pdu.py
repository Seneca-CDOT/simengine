from enginecore.state.api.state import IStateManager
from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IPDUStateManager(IStateManager):
    """Handles state logic for PDU asset """
