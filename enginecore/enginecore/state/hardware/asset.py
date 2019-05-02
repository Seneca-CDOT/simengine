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


class Asset(Component):
    """Abstract Asset Class """

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
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
            load_change=load_change,
            old_load=old_load,
            new_load=new_load,
            asset_key=self.state.key,
        )

    @handler("ChildAssetPowerUp", "ChildAssetLoadIncreased")
    def on_load_increase(self, event, *args, **kwargs):
        """Load is ramped up if child is powered up or child asset's load is increased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        increased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was increased by {}, new load={};"
        return self._update_load(increased_by, lambda old, change: old + change, msg)

    @handler("ChildAssetPowerDown", "ChildAssetLoadDecreased")
    def on_load_decrease(self, event, *args, **kwargs):
        """Load is decreased if child is powered off or child asset's load is decreased
        Returns: 
            LoadEventResult: details on the asset state updates
        """

        decreased_by = kwargs["child_load"]
        msg = "Asset:[{}] load {} was decreased by {}, new load={};"
        return self._update_load(decreased_by, lambda old, change: old - change, msg)

    @handler("VoltageIncreased")
    def on_voltage_increase(self, event, *args, **kwargs):
        """Handle input power voltage increase"""
        e_result = event_results.VoltageEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_voltage=kwargs["old_value"],
            new_voltage=kwargs["new_value"],
        )

        min_voltage, _ = self.state.min_voltage_prop()

        if kwargs["new_value"] >= min_voltage and not self.state.status:
            self.state.power_up()
            self.state.publish_power()
            event.success = False

        return e_result

    @handler("VoltageDecreased")
    def on_voltage_decrease(self, event, *args, **kwargs):
        """Handle input power voltage drop"""

        e_result = event_results.VoltageEventResult(
            asset_key=self.state.key,
            asset_type=self.state.asset_type,
            old_voltage=kwargs["old_value"],
            new_voltage=kwargs["new_value"],
        )

        min_voltage, power_off_timeout = self.state.min_voltage_prop()
        if kwargs["new_value"] < min_voltage and self.state.status:

            if power_off_timeout:
                time.sleep(power_off_timeout)

            self.state.power_off()
            self.state.publish_power()
            event.success = False

        return e_result

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS
