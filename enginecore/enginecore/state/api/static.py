from enginecore.state.api.state import IStateManager
from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IStaticDeviceStateManager(IStateManager):
    """Exposes state logic for static(dummy) asset """

    @Randomizer.randomize_method()
    def shut_down(self):
        powered = super().shut_down()
        if not powered:
            self._update_load(0.0)
        return powered

    @Randomizer.randomize_method()
    def power_off(self):
        powered = super().power_off()
        if not powered:
            self._update_load(0.0)
        return powered

    @Randomizer.randomize_method()
    def power_up(self):
        powered = super().power_up()
        if powered:
            self._update_load(self.power_usage)
        return powered
