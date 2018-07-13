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
            "1": events.AssetPowerUp(),
        }[value]

    @classmethod
    def map_child_event(cls, value, new_load, child_key):
        return { 
            "0": events.ChildAssetPowerDown(child_key=child_key, child_load=new_load),
            "1": events.ChildAssetPowerUp(child_key=child_key, child_load=new_load),
        }[value]

    @classmethod
    def map_parent_event(cls, value):
        return {
            "0": events.ParentAssetPowerDown(),
            "1": events.ParentAssetPowerUp() 
        }[value]

    @classmethod
    def map_load_increased_by(cls, new_load, child_key):
        return events.ChildAssetLoadIncreased(child_load=new_load, child_key=child_key)
    
    @classmethod
    def map_load_decreased_by(cls, new_load, child_key):
        return events.ChildAssetLoadDecreased(child_load=new_load, child_key=child_key)