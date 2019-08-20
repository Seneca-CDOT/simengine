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

    def on_power_off_request_received(self, event, *args, **kwargs):
        """Powers off on parent offline"""
        return self.power_off()

    def on_power_up_request_received(self, event, *args, **kwargs):
        """Powers on on parent going online"""
        return self.power_up()

    @handler("VoltageIncreased", "VoltageDecreased", priority=-2)
    def on_voltage_power_source_change(self, event, *args, **kwargs):
        """Handle input power voltage increase"""
        self.state.update_load(self.state.power_usage)


@register_asset
class Lamp(StaticAsset):
    """A simple demonstration type """

    channel = "engine-lamp"
