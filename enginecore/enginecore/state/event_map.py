""" Maps redis events to circuit events """
from enginecore.state.hardware import asset_events as events


class PowerEventMap:
    """This helper maps redis values of OIDs or asset states to circuit events """

    STATE_SPECS = {
        "OutletState": {
            "switchOff": events.SignalDown(),
            "switchOn": events.SignalUp(),
            "immediateReboot": events.SignalReboot(),
            "delayedOff": events.SignalDown(delayed=True),
            "delayedOn": events.SignalUp(delayed=True),
        },
        "PowerOff": {
            "switchOff": events.SignalDown(),
            "switchOffGraceful": events.SignalDown(graceful=True),
        },
    }

    @classmethod
    def get_state_specs(cls):
        """Map OID & their values to events"""
        return PowerEventMap.STATE_SPECS

    @classmethod
    def map_asset_event(cls, value):
        """Map redis asset values to events"""
        return {0: events.ButtonPowerDownPressed(), 1: events.ButtonPowerUpPressed()}[
            value
        ]

    @classmethod
    def map_child_event(cls, value, new_load, child_key):
        """Map child redis updates to events"""
        return {
            0: events.ChildAssetPowerDown(child_key=child_key, child_load=new_load),
            1: events.ChildAssetPowerUp(child_key=child_key, child_load=new_load),
        }[value]

    @classmethod
    def map_parent_event(cls, value):
        """Map parent redis updates to events"""
        return {0: events.ParentAssetPowerDown(), 1: events.ParentAssetPowerUp()}[value]

    @classmethod
    def map_load_increased_by(cls, new_load, child_key):
        """Child asset load increased"""
        return events.ChildAssetLoadIncreased(child_load=new_load, child_key=child_key)

    @classmethod
    def map_load_decreased_by(cls, new_load, child_key):
        """Child asset load dropped"""
        return events.ChildAssetLoadDecreased(child_load=new_load, child_key=child_key)

    @classmethod
    def map_mains_event(cls, value):
        """Map parent redis updates to events"""
        return {0: events.PowerOutage(), 1: events.PowerRestored()}[value]

    @classmethod
    def map_ambient_event(cls, old_value, new_value):
        """Ambient changes"""
        return (
            events.AmbientDecreased
            if old_value > new_value
            else events.AmbientIncreased
        )(old_value=old_value, new_value=new_value)

    @classmethod
    def map_voltage_event(cls, source_key, old_value, new_value):
        """Voltage changes"""
        return (
            events.VoltageDecreased
            if old_value > new_value or new_value == 0
            else events.VoltageIncreased
        )(source_key=source_key, old_value=old_value, new_value=new_value)
