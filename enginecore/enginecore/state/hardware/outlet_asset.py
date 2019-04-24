"""Event handler for outlet
Includes both wall-powered outlet and a output power outlet for UPS/PDU
"""
# **due to circuit callback signature
# pylint: disable=W0613

import time

from circuits import handler

import enginecore.state.hardware.state_managers as sm
from enginecore.state.hardware.asset import Asset
from enginecore.state.hardware import event_results

from enginecore.state.hardware.asset_definition import register_asset


@register_asset
class Outlet(Asset):

    channel = "engine-outlet"
    StateManagerCls = sm.OutletStateManager

    def __init__(self, asset_info):
        super(Outlet, self).__init__(Outlet.StateManagerCls(asset_info))

    ##### React to any events of the connected components #####

    @handler("SignalDown", priority=1)
    def on_signal_down_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state 
        (if if one is updated, other ones should be updated as well)"""
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOff)

    @handler("SignalUp", priority=1)
    def on_signal_up_received(self, event, *args, **kwargs):
        """Outlet may have multiple OIDs associated with the state"""
        self.state.set_parent_oid_states(sm.OutletStateManager.OutletState.switchOn)

    @handler("ParentAssetPowerDown", "SignalDown")
    def on_power_off_request_received(self, event, *args, **kwargs):
        """ React to events with power down """
        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_off_delay())

        return self.power_off()

    @handler("ParentAssetPowerUp", "SignalUp")
    def on_power_up_request_received(self, event, *args, **kwargs):
        """ React to events with power up """

        if "delayed" in kwargs and kwargs["delayed"]:
            time.sleep(self.state.get_config_on_delay())

        e_result = self.power_up()
        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("SignalReboot")
    def on_reboot_request_received(self, event, *args, **kwargs):
        """Received reboot request"""
        old_state = self.state.status

        self.power_off()
        e_result_up = self.power_up()
        if not e_result_up.new_state:
            event.success = False

        return event_results.PowerEventResult(
            old_state=old_state,
            new_state=e_result_up.new_state,
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
        )
