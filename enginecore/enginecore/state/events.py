""" Events """
from circuits import Event

class ButtonPowerDownPressed(Event):
    """ On Asset Did Power Down """

class ButtonPowerUpPressed(Event):
    """ On Asset Did Power Up """

class ParentAssetPowerDown(Event):
    """ On Parent Did Go Down """
    success = True
    
class ParentAssetPowerUp(Event):
    """ On Parent Did Go Up """
    success = True
    
class ChildAssetPowerDown(Event):
    """ On Child Did Go Down """
    success = True
    
class ChildAssetPowerUp(Event):
    """ On Child Did Go Up """
    success = True

class ChildAssetLoadIncreased(Event):
    """ On Child Load Change"""
    success = True

class ChildAssetLoadDecreased(Event):
    """ On Child Load Change"""    
    success = True

class SignalDown(Event):
    """ Asset Received power down request """
    success = True

class SignalUp(Event):
    """ Asset Received power Up request """
    success = True

class SignalReboot(Event):
    """ Asset Received reboot request """
    success = True
    