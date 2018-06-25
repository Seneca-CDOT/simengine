""" Events """
from circuits import Event

class AssetPowerDown(Event):
    """ On Asset Did Power Down """

class AssetPowerUp(Event):
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
    
class ChildAssetLoadUpdate(Event):
    """ On Load Update """
    success = True

class SignalDown(Event):
    """ Asset Received power down request """
    success = True

class SignalUp(Event):
    """ Asset Received power Up request """
    success = True
