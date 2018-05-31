""" Maps redis events to circuit events """
import enginecore.state.events as events

event_map = {
    'outlet': {
        "0": events.OutletPowerDown(),
        "1": events.OutletPowerUp(),
    },
    'pdu': {
        "0": events.PDUPowerDown(),
        "1": events.PDUPowerUp(),
    }
}