"""Asset manages runtime state of a hardware component/device
& responds to certain events (Power/Thermal etc.)
"""
# **due to circuit callback signature
# pylint: disable=W0613

import logging
import os
from circuits import Component, handler
from enginecore.state.hardware.asset_definition import SUPPORTED_ASSETS
from enginecore.state.state_initializer import get_temp_workplace_dir

logger = logging.getLogger(__name__)


class Asset(Component):
    """Top asset component that aggregates behaviour shared
    among all hardware devices; (all hardware assets must derive
    from here)"""

    def __init__(self, state):
        super(Asset, self).__init__()
        self._state = state
        self._state_reason = None
        self.state.update_input_voltage(0)

        self.state.reset_boot_time()
        self.state.update_load(0.0)

    @property
    def key(self):
        """ Get ID assigned to the asset """
        return self.state.key

    @property
    def state(self):
        """State manager instance"""
        return self._state

    @property
    def state_reason(self):
        """Reason for asset power state"""
        return self._state_reason

    @state_reason.setter
    def state_reason(self, value):
        self._state_reason = value

    def _update_load(self, new_load):
        """Update load for this asset"""
        return self.state.update_load(new_load)

    def power_up(self, state_reason=None):
        """Power up this asset
        Args:
            state_reason(PowerStateReason): reason for powering
                this asset (e.g. due to AC restored or user
                pressing button etc.)
        Returns: 
            int: new state after power_up operation
        """
        if not state_reason:
            state_reason = self.state.PowerStateReason.ac_restored

        self._state_reason = state_reason
        return self.state.power_up()

    def power_off(self, state_reason=None):
        """Power down this asset 
        Args:
            state_reason(PowerStateReason): reason for poweroff
                (e.g. due to AC loss)
        Returns: 
            int: new state after power_up operation
        """
        if not state_reason:
            state_reason = self.state.PowerStateReason.ac_lost

        self._state_reason = state_reason
        return self.state.power_off()

    def shut_down(self, state_reason=None):
        """Shut down this asset (graceful shutdown)
        Args:
            state_reason(PowerStateReason): reason for shutdown
        Returns: 
            int: new state after power_up operation
        """
        if not state_reason:
            state_reason = self.state.PowerStateReason.turned_off

        self._state_reason = state_reason
        return self.state.shut_down()

    def _create_asset_workplace_dir(self):
        """Create temp workplace directory for the asset 
        (under /tmp/$SIMENGINE_WORKPLACE_TEMP/<asset_key>)
        Returns:
            str: path to newly created asset directory
        """
        asset_dir = os.path.join(get_temp_workplace_dir(), str(self.key))
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)

        return asset_dir

    def _process_parent_volt_e(self, event):
        """Process parent voltage event by analyzing if voltage is 
        within the accepted threshold and if asset power state 
        needs to be changed"""

        asset_event = event.get_next_power_event(self)

        min_voltage = self.state.min_voltage_prop()
        powered_off_by_user = (
            self._state_reason == self.state.PowerStateReason.turned_off
        )
        power_action = None

        old_out_volt, new_out_volt = asset_event.out_volt.old, asset_event.out_volt.new

        # check new input voltage
        # Asset is underpowered (volt is too low)
        if new_out_volt <= min_voltage and asset_event.state.old:
            power_action = self.power_off

        # Asset was offline and underpowered, power back up
        elif (
            new_out_volt > min_voltage
            and not asset_event.state.old
            and not powered_off_by_user
            and self.state.power_on_ac_restored
        ):
            power_action = self.power_up

        # re-set output voltage values in case of power condition
        if power_action:
            asset_event.state.new = power_action()
            asset_event.out_volt.old = old_out_volt * asset_event.state.old
            asset_event.out_volt.new = new_out_volt * asset_event.state.new

        if self.state.status or not asset_event.state.unchanged():
            asset_event.calc_load_from_volt()
            if not asset_event.load.unchanged():
                self._update_load(
                    self.state.load - asset_event.load.old + asset_event.load.new
                )

        return asset_event

    @handler("ChildLoadUpEvent", "ChildLoadDownEvent")
    def on_child_load_update(self, event, *args, **kwargs):
        """Process child asset load changes by updating load of this device
        Args:
            event(ChildLoadEvent): load event associated with a child node
                                   powered by this asset
        Returns:
            AssetLoadEvent: contains load update details for this asset
        """
        asset_load_event = event.get_next_load_event(self)
        new_load = asset_load_event.load.old + event.load.difference

        self._update_load(new_load)
        asset_load_event.load.new = new_load
        return asset_load_event

    @handler("AmbientUpEvent", "AmbientDownEvent")
    def on_ambient_updated(self, event, *args, **kwargs):
        """Process Ambient temperature changes"""
        return event

    @handler("PowerButtonOnEvent", "PowerButtonOffEvent", priority=10)
    def set_redis_state_on_btn_press(self, event, *args, **kwargs):
        """Update redis state once request goes through
        (higher priority means it will be called first)
        """
        self._state_reason = {
            "PowerButtonOnEvent": self.state.PowerStateReason.turned_on,
            "PowerButtonOffEvent": self.state.PowerStateReason.turned_off,
        }[event.name]

        self.state.set_redis_asset_state(event.state.new)

    @handler("PowerButtonOnEvent", "PowerButtonOffEvent")
    def on_power_button_press(self, event, *args, **kwargs):
        """React to power button event by notifying engine of
        state changes associated with it"""
        asset_event = event.get_next_power_event()
        asset_event.calc_load_from_volt()
        return asset_event

    @handler("InputVoltageUpEvent", "InputVoltageDownEvent", priority=-1)
    def detect_input_voltage(self, event, *args, **kwargs):
        """Update input voltage
        (called after every other handler due to priority set to -1)
        """
        self.state.update_input_voltage(event.in_volt.new)
        logger.debug(
            "VOLTAGE %s %s, in[%s]", event.name, self.key, self.state.input_voltage
        )

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        """React to input voltage spike;
        Asset can power up on volt increase if it was offline;
        Args:
            event(InputVoltageUpEvent): input voltage event indicating
                                        that source voltage has increased
        Returns:
            AssetPowerEvent: event indicating possible power changes due to 
                             voltage change (e.g. load, power state changes etc.)
        """
        return self._process_parent_volt_e(event)

    @handler("InputVoltageDownEvent")
    def on_input_voltage_down(self, event, *args, **kwargs):
        """React to input voltage drop;
        Asset can power off if input voltage drops below the acceptable
        threshold.
        Args:
            event(InputVoltageDownEvent): input voltage event indicating
                                          that source voltage has dropped
        Returns:
            AssetPowerEvent: event indicating possible power changes due to 
                             voltage change (e.g. load, power state changes etc.)
        """
        return self._process_parent_volt_e(event)

    def __str__(self):
        return self.state.__str__()

    def stop(self, code=None):
        """Gracefully stop asset by closing all the connections,
        agents (if supported) and joining threads
        """
        self.state.close_connection()
        super().stop(code)

    @classmethod
    def get_supported_assets(cls):
        """Get factory containing registered assets"""
        return SUPPORTED_ASSETS
