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

class ChildAssetPowerUp(Event):
    """ On Child Did Go Up """

class SignalDown(Event):
    pass

class SignalUp(Event):
    pass

class LoadUpdate(Event):
    pass