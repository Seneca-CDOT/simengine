"""SUPPORTED_ASSETS keeps track of all the hardware assets
(so that asset type in data store can be mapped to a python class);
Assets can be added to the map by suppyling register_asset as
a decorator to some asset class e.g:

@register_asset
class Server(circuits.Component):
    pass
"""
SUPPORTED_ASSETS = {}


def register_asset(cls):
    """
    This decorator maps string class names to classes
    (It is basically a factory)
    """
    SUPPORTED_ASSETS[cls.__name__.lower()] = cls
    return cls
