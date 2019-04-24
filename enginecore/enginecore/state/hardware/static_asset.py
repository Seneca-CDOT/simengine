"""Event handling logic for "dummy" device types drawing power;
"""
# **due to circuit callback signature
# pylint: disable=W0613

from circuits import handler
import enginecore.state.hardware.state_managers as sm
from enginecore.state.hardware.asset import Asset

from enginecore.state.hardware.asset_definition import register_asset


@register_asset
class StaticAsset(Asset):

    channel = "engine-static"
    StateManagerCls = sm.StaticDeviceStateManager

    def __init__(self, asset_info):
        super(StaticAsset, self).__init__(self.StateManagerCls(asset_info))
        self.state.update_load(self.state.power_usage)

    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Powers off on parent offline"""
        return self.power_off()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self):
        """Powers on on parent going online"""
        return self.power_up()


@register_asset
class Lamp(StaticAsset):
    """A simple demonstration type """

    channel = "engine-lamp"
