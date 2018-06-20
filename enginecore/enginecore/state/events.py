""" Events """
from circuits import Event

class AssetPowerDown(Event):
    """ On Asset Did Receive PowerDown Signal """

class AssetPowerUp(Event):
    """ On Asset Did Receive PowerUp Signal """

class ParentAssetPowerDown(Event):
    """ On Parent Did Go Down """

class ParentAssetPowerUp(Event):
    """ On Parent Did Go Up """

class ChildAssetPowerDown(Event):
    """ On Child Did Go Down """
    success = True
    
class ChildAssetPowerUp(Event):
    """ On Child Did Go Up """
    success = True
    
class LoadUpdate(Event):
    """ On Load Update """
    success = True

    
class SignalDown(Event):
    pass

class SignalUp(Event):
    pass

