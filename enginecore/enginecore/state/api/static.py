from enginecore.state.api.state import IStateManager


class IStaticDeviceManager(IStateManager):
    """Exposes state logic for static(dummy) asset """
  
    def power_up(self):
        powered = super().power_up()
        if powered:
            self._update_load(self.power_usage)
        return powered
