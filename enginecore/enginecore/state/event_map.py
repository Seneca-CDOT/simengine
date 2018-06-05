""" Maps redis events to circuit events """
import enginecore.state.events as events

event_map = {
    'pdu': {
        "0": events.PDUPowerDown(),
        "1": events.PDUPowerUp(),
    },     
    'outlet': {
        "0": events.OutletPowerDown(),
        "1": events.OutletPowerUp(),
    }, 
    ## Outlet OIDS
    'OutletState': {
        "0": events.SignalDown(),
        "1": events.SignalUp(),
    }
}