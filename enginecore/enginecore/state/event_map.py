""" Maps redis events to circuit events """
import enginecore.state.events as events


class PowerEventManager:

    STATE_SPECS = {
        'OutletState': {
            "switchOff": events.SignalDown(),
            "switchOn": events.SignalUp()
        }
    }


    @classmethod
    def get_state_specs(cls):
        return PowerEventManager.STATE_SPECS

    @classmethod
    def map_asset_event(cls, value):
        return {
            "0": events.AssetPowerDown(),
            "1": events.AssetPowerDown(),
        }[value]

    @classmethod
    def map_parent_event(cls, value):
        return {
            "0": events.ParentAssetPowerDown(),
            "1": events.ParentAssetPowerUp() 
        }[value]