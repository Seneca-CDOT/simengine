""" Events """
from circuits import Event

class OutletPowerDown(Event):
    """ Power down event """

class OutletPowerUp(Event):
    """ Power up event """

class PDUPowerDown(Event):
    """ Power down event """

class PDUPowerUp(Event):
    """ Power up event """

class SignalDown(Event):
    pass

class SignalUp(Event):
    pass