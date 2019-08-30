"""Event handler for outlet
Includes both wall-powered outlet and a output power outlet for UPS/PDU
"""
# **due to circuit callback signature
# pylint: disable=W0613

import time

from circuits import handler

import enginecore.state.hardware.internal_state as in_state
from enginecore.state.hardware.asset import Asset

from enginecore.state.hardware.asset_definition import register_asset


@register_asset
class Outlet(Asset):
    """Hardware manger for outlet asset; some outlets that are not of wallpower type
    (e.g. output outlets belonging to UPS/PDU) can handle SNMP signals for powering
    down/up or reboot
    """

    channel = "engine-outlet"
    StateManagerCls = in_state.OutletStateManager

    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))

    ##### React to any events of the connected components #####

    @handler("SignalDownEvent", priority=1)
    def on_signal_down_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state 
        (if if one is updated, other ones should be updated as well)"""
        self.state.set_parent_oid_states(
            in_state.OutletStateManager.OutletState.switchOff
        )

    @handler("SignalUpEvent", priority=1)
    def on_signal_up_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state"""
        self.state.set_parent_oid_states(
            in_state.OutletStateManager.OutletState.switchOn
        )

    @handler("SignalDownEvent")
    def on_power_off_request_received(self, event, *args, **kwargs):
        """ React to events with power down """
        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_off_delay())

        asset_event = event.get_next_power_event(self)
        asset_event.state.new = self.power_off()

        return asset_event

    @handler("SignalUpEvent")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """ React to events with power up """

        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_on_delay())

        asset_event = event.get_next_power_event(self)
        asset_event.state.new = self.power_up()

        return asset_event

    @handler("SignalRebootEvent")
    def on_reboot_request_received(self, event, *args, **kwargs):
        """Received reboot request"""
        asset_event = event.get_next_power_event(self)

        self.power_off()
        asset_event.state.new = self.power_up()

        return asset_event
