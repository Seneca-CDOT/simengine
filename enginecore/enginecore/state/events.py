"""Contains list of events dispatched by the main listener """
from circuits import Event

# Power Events -------

class ButtonPowerDownPressed(Event):
    """On Asset Did Power Down (equivalent to power button press) """

class ButtonPowerUpPressed(Event):
    """On Asset Did Power Up  (equivalent to power button press) """

class ParentAssetPowerDown(Event):
    """On Parent Did Go Down """
    success = True
    
class ParentAssetPowerUp(Event):
    """On Parent Did Go Up """
    success = True
    
class ChildAssetPowerDown(Event):
    """On Child Did Go Down """
    success = True
    
class ChildAssetPowerUp(Event):
    """On Child Did Go Up """
    success = True

class ChildAssetLoadIncreased(Event):
    """On Child Load Change"""
    success = True

class ChildAssetLoadDecreased(Event):
    """On Child Load Change"""    
    success = True

class SignalDown(Event):
    """Asset Received power down request/command """
    success = True

class SignalUp(Event):
    """Asset Received power Up request/command """
    success = True

class SignalReboot(Event):
    """Asset Received reboot request/command """
    success = True

class PowerOutage(Event):
    """On Power Outage"""
    pass

class PowerRestored(Event):
    """On power (mains source) restored"""
    pass

# Thermal Events -------

class AmbientIncreased(Event):
    """Ambient went up"""
    pass

class AmbientDecreased(Event):
    """Ambient temperature dropped"""
    pass
