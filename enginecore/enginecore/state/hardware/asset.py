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
        """Reason for asset power state"""
        return self._state_reason

    @state_reason.setter
    def state_reason(self, value):
        self._state_reason = value
        # logging.info(
        #     "Asset:[%s][%s] due to event <%s>",
        #     self.key,
        #     "online" if self.state.status else "offline",
        #     value.__name__,
        # )

    @property
    def power_state_caused_by_user(self):
        """Returns true if user powered down/up the asset (and not AC power event)"""
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

    def _update_load(self, load_change, arithmetic_op):
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
        return self._update_load(increased_by, lambda old, change: old + change)

    @handler("ChildAssetLoadDecreased", "ChildAssetPowerDown")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        decreased_by = kwargs["child_load"]
        return self._update_load(decreased_by, lambda old, change: old - change)

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

    def _get_load_event_result(self, volt_event_details, power_e_result=None):
        """Get formatted load event result"""

        old_volt, new_volt = (
            volt_event_details["old_value"],
            volt_event_details["new_value"],
        )
        calc_load = lambda v: self.state.power_consumption / v if v else 0

        # print(self.state)
        # Output voltage can still be 0 for some assets even though
        # their input voltage > 0
        # (most devices require at least 90V-100V in order to function)
        old_out_volt = old_volt * (power_e_result.old_state if power_e_result else 1)
        new_out_volt = new_volt * (power_e_result.new_state if power_e_result else 1)

        old_load, new_load = (calc_load(volt) for volt in [old_out_volt, new_out_volt])
        # print(old_load)

        # old_load = self.state.load  # TODO: remove old load from above calculations
        # print(old_load)

        if old_load == new_load == 0:
            return None

        return [
            event_results.LoadEventResult(
                asset_key=self.state.key,
                asset_type=self.state.asset_type,
                parent_key=volt_event_details["source_key"],
                old_load=old_load,
                new_load=new_load,
            )
        ]

    def _process_parent_volt_e(self, kwargs):

        calc_load = lambda v: self.state.power_consumption / v if v else 0
        state = {
            "new_state": int(kwargs["new_in_volt"] != 0),
            "old_state": int(kwargs["old_in_volt"] != 0),
        }

        new_out_volt = kwargs["new_in_volt"] * state["new_state"]
        old_out_volt = kwargs["old_in_volt"] * state["old_state"]

        min_voltage = self.state.min_voltage_prop()

        if kwargs["new_in_volt"] <= min_voltage and self.state.status:
            state["new_state"] = self.state.power_off()
        elif kwargs["new_in_volt"] > min_voltage and not self.state.status:
            state["new_state"] = self.state.power_up()

        old_load, new_load = (calc_load(volt) for volt in [old_out_volt, new_out_volt])
        return {
            "key": self.key,
            "voltage": {"new_out_volt": new_out_volt, "old_out_volt": old_out_volt},
            "state": state,
            "load": {"new_load": new_load, "old_load": old_load},
        }

    @handler("InputVoltageUpEvent", "InputVoltageDownEvent", priority=-1)
    def detect_input_voltage(self, event, *args, **kwargs):
        """Update input voltage"""
        self.state.update_input_voltage(kwargs["new_in_volt"])
        print(
            "VOLTAGE {} {}, in[{}]".format(
                event.name, self.key, self.state.input_voltage
            )
        )

    @handler("InputVoltageUpEvent")
    def on_parent_volt_up(self, event, *args, **kwargs):
        print("[ASSET] parent volt up")
        print("         parent event -> ", event)
        return self._process_parent_volt_e(kwargs)

    @handler("InputVoltageDownEvent")
    def on_parent_volt_down(self, event, *args, **kwargs):
        print("[ASSET] parent volt down")
        print("         parent event -> ", event)

        return self._process_parent_volt_e(kwargs)

    @handler("VoltageIncreased")
    def on_voltage_increase(self, event, *args, **kwargs):
        """React to input voltage spike;
        Asset can power up on volt increase if it was down, event propagation
        gets cancelled if asset's state doesn't change

        Returns:
            tuple: 3 event results:
                VoltageEventResult : to be propagated to this asset's children
                PowerEventResult   : asset power state changes if any
                LoadEventResult    : load change (to be propagated up the power stream)
        """

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

        load_event_result = self._get_load_event_result(kwargs, power_event_result)
        return volt_event_result, power_event_result, load_event_result

    @handler("VoltageDecreased")
    def on_voltage_decrease(self, event, *args, **kwargs):
        """React to input voltage drop;
        Asset can power off if input voltage drops below the acceptable
        threshold. Event propagation gets cancelled if no state changes
        occured.

        Returns:
            tuple: 3 event results:
                VoltageEventResult : to be propagated to this asset's children
                PowerEventResult   : asset power state changes if any
                LoadEventResult    : load change (to be propagated up the power stream)
        """

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

        load_event_result = self._get_load_event_result(kwargs, power_event_result)
        return volt_event_result, power_event_result, load_event_result

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
