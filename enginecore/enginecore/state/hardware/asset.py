"""Asset manages runtime state of a hardware component/device
& responds to certain events (Power/Thermal etc.)
"""
# **due to circuit callback signature
# pylint: disable=W0613

import logging
import time

from circuits import Component, handler
from enginecore.state.hardware import event_results
from enginecore.state.hardware.asset_definition import SUPPORTED_ASSETS
from enginecore.state.hardware import asset_events


class Asset(Component):
    """Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self._state_reason = asset_events.ButtonPowerUpPressed
        self.state.update_input_voltage(0)

        self.state.reset_boot_time()
        self.state.update_load(0)

    @property
    def key(self):
        """ Get ID assigned to the asset """
        return self.state.key

    @property
    def state(self):
        """State manager instance"""
        return self._state

    @property
    def power_on_when_ac_restore(self):
        """Indicates if asset should power up when input power is present"""
        return True

    @property
    def state_reason(self):
        """"""
        return self._state_reason

    @state_reason.setter
    def state_reason(self, value):
        """"""
        self._state_reason = value
        # logging.info(
        #     "Asset:[%s][%s] due to event <%s>",
        #     self.key,
        #     "online" if self.state.status else "offline",
        #     value.__name__,
        # )

    @property
    def power_state_caused_by_user(self):
        """"""
        return (
            self.state_reason == asset_events.ButtonPowerDownPressed
            or self.state_reason == asset_events.ButtonPowerUpPressed
        )

    def power_up(self):
        """Power up this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return event_results.PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            load_change=0,
            new_state=self.state.power_up(),
        )

    def shut_down(self):
        """Shut down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return event_results.PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            load_change=0,
            new_state=self.state.shut_down(),
        )

    def power_off(self):
        """Power down this asset 
        Returns: 
            PowerEventResult: tuple indicating asset key, type, old & new states
        """
        old_state = self.state.status
        return event_results.PowerEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_state=old_state,
            new_state=self.state.power_off(),
        )

    def _update_load(self, load_change, arithmetic_op, msg=""):
        """React to load changes by updating asset load
        
        Args:
            load_change(float): how much AMPs need to be added/subtracted
            arithmetic_op(callable): calculates new load
                                     (receives old load & measured load change)
            msg(str): message to be printed
        
        Returns:
            LoadEventResult: Event result containing old 
                             & new load values as well as value subtracted/added
        """

        old_load = self.state.load
        new_load = arithmetic_op(old_load, load_change)

        if msg:
            logging.info(msg.format(self.state.key, old_load, load_change, new_load))

        self.state.update_load(new_load)

        return event_results.LoadEventResult(
            old_load=old_load, new_load=new_load, asset_key=self.state.key
        )

    @handler("ChildAssetLoadIncreased", "ChildAssetPowerUp")
    def on_load_increase(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        increased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was increased by {}, new load={};"
        return self._update_load(increased_by, lambda old, change: old + change, msg)

    @handler("ChildAssetLoadDecreased", "ChildAssetPowerDown")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        decreased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was decreased by {}, new load={};"
        return self._update_load(decreased_by, lambda old, change: old - change, msg)

    @handler("ButtonPowerDownPressed")
    def on_btn_power_down(self, event):
        """When user presses power button to turn asset off"""
        self.state_reason = asset_events.ButtonPowerDownPressed

    @handler("ButtonPowerUpPressed")
    def on_btn_power_up(self, event):
        """When user preses power button to turn asset on"""
        self.state_reason = asset_events.ButtonPowerUpPressed

    def _get_voltage_event_result(self, event_details):
        """Get formatted voltage event result"""

        return event_results.VoltageEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_voltage=event_details["old_value"],
            new_voltage=event_details["new_value"],
        )

    @handler("VoltageIncreased", "VoltageDecreased", priority=-1)
    def detect_input_voltage(self, event, *args, **kwargs):
        """Update input voltage"""
        self.state.update_input_voltage(kwargs["new_value"])
        print(
            "VOLTAGE {} {}, in[{}]".format(
                event.name, self.key, self.state.input_voltage
            )
        )

    @handler("VoltageIncreased")
    def on_voltage_increase(self, event, *args, **kwargs):
        """Handle input power voltage increase"""

        power_event_result = None
        volt_event_result = self._get_voltage_event_result(kwargs)

        min_voltage = self.state.min_voltage_prop()

        # power up asset it has died previously due to underpower
        if (
            kwargs["new_value"] > min_voltage
            and not self.state.status
            and not self.power_state_caused_by_user
        ):
            power_event_result = self.on_power_up_request_received(event, args, kwargs)
            if power_event_result.new_state != power_event_result.old_state:
                self.state_reason = asset_events.VoltageIncreased

        if not self.state.status:
            event.success = False

        return volt_event_result, power_event_result

    @handler("VoltageDecreased")
    def on_voltage_decrease(self, event, *args, **kwargs):
        """Handle input power voltage drop"""

        power_event_result = None
        volt_event_result = self._get_voltage_event_result(kwargs)

        # asset was already powered down, no need to propagate voltage
        if not self.state.status and self.power_state_caused_by_user:
            event.success = False

        # does asset need to be powered down due to low voltage?
        min_voltage = self.state.min_voltage_prop()
        if kwargs["new_value"] <= min_voltage and self.state.status:
            power_event_result = self.on_power_off_request_received(event, args, kwargs)
            if power_event_result.new_state != power_event_result.old_state:
                self.state_reason = asset_events.VoltageDecreased

        return volt_event_result, power_event_result

    def on_power_up_request_received(self, event, *args, **kwargs):
        """Called on voltage spike"""
        raise NotImplementedError

    def on_power_off_request_received(self, event, *args, **kwargs):
        """Called on voltage drop"""
        raise NotImplementedError

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS
