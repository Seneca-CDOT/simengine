from enginecore.state.api.state import IStateManager
from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IStaticDeviceManager(IStateManager):
    """Exposes state logic for static(dummy) asset """

    @property
    def power_usage(self):
        return self._asset_info["powerConsumption"] / self._asset_info["powerSource"]

    @Randomizer.randomize_method()
    def power_up(self):
        powered = super().power_up()
        if powered:
            self._update_load(self.power_usage)
        return powered
