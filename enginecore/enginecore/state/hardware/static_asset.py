"""Event handling logic for "dummy" device types drawing power;
"""
# **due to circuit callback signature
# pylint: disable=W0613

from circuits import handler
import enginecore.state.hardware.internal_state as in_state
from enginecore.state.hardware.asset import Asset

from enginecore.state.hardware.asset_definition import register_asset


@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = in_state.StaticDeviceStateManager

    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))


@register_asset
class Lamp(StaticAsset):
    """A simple demonstration type """

    channel = "engine-lamp"
