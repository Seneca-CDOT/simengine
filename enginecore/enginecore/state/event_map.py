""" Maps redis events to circuit events """
import enginecore.state.events as events

STATE_SPECS = {
    'OutletState': {
        "switchOff": events.SignalDown(),
        "switchOn": events.SignalUp()
    }
}

event_map = {
    'pdu': {
        "0": events.PDUPowerDown(),
        "1": events.PDUPowerUp(),
    },     
    'outlet': {
        "0": events.OutletPowerDown(),
        "1": events.OutletPowerUp(),
    },
    'staticasset': {
        "0": events.LoadUpdate(),
        "1": events.LoadUpdate()
    }
}