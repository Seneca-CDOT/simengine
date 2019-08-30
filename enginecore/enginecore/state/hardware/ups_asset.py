"""Event handler for UPS (Uninterrupted power supply)
UPS asset supports snmp interface & manages power source for the output power stream
For example, it switches to battery if upstream power is offline or voltage is too low
"""
# **due to circuit callback signature
# pylint: disable=W0613

import logging
import json
import math
from datetime import datetime as dt

from threading import Thread, Event
from circuits import handler
import enginecore.state.hardware.internal_state as in_state
from enginecore.state.hardware.asset import Asset
from enginecore.state.hardware.snmp_asset import SNMPSim
from enginecore.state.api.environment import ISystemEnvironment

from enginecore.state.hardware.asset_definition import register_asset

logger = logging.getLogger(__name__)


@register_asset
class UPS(Asset, SNMPSim):
    """Provides reactive logic for UPS & manages snmp simulator instance

    Example:
        drains battery when upstream power becomes unavailable 
        charges battery when upstream power is restored
    """

    channel = "engine-ups"
    StateManagerCls = in_state.UPSStateManager

    def __init__(self, asset_info):
        Asset.__init__(self, state=UPS.StateManagerCls(asset_info))
        SNMPSim.__init__(self, self._state)

        # remove default logic for handling input voltage updates
        super().removeHandler(super().on_input_voltage_up)
        super().removeHandler(super().on_input_voltage_down)
        super().removeHandler(super().on_child_load_update)
        super().removeHandler(super().on_power_button_press)
        super().removeHandler(super().set_redis_state_on_btn_press)

        self._low_volt_th_oid = self.state.get_oid_by_name("AdvConfigLowTransferVolt")

        # Store known { wattage: time_remaining } key/value pairs (runtime graph)
        self._runtime_details = json.loads(asset_info["runtime"])

        # Track upstream power availability
        self._charge_speed_factor = 1
        self._drain_speed_factor = 1

        # Threads responsible for battery charge/discharge
        self._battery_drain_t = None
        self._battery_charge_t = None
        self._stop_event = Event()

        self._start_time_battery = None

        # set battery level to max
        self.state.update_battery(self.state.battery_max_level)

        # get charge per second using full recharge time (hrs)
        self._charge_per_second = self.state.battery_max_level / (
            self.state.full_recharge_time * 60 * 60
        )

    def _cacl_time_left(self, wattage):
        """Approximate runtime estimation based on current battery level"""
        return (
            self._calc_full_power_time_left(wattage) * self.state.battery_level
        ) / self.state.battery_max_level

    def _calc_full_power_time_left(self, wattage):
        """Approximate runtime estimation for the fully-charged battery"""

        # Prevent from TimeTick value failing bounding constraints
        if wattage < 0.1:
            wattage = 0.1

        close_wattage = min(self._runtime_details, key=lambda x: abs(int(x) - wattage))
        close_timeleft = self._runtime_details[close_wattage]

        # inverse proportion, calculate full power time left
        fp_time_left = (close_timeleft * int(close_wattage)) / wattage

        # see if input voltage is present -> adjust time left
        lower_threshold = int(self.state.get_oid_value(self._low_volt_th_oid))
        in_voltage = self.state.input_voltage

        if 0 < in_voltage <= lower_threshold:
            fp_time_left += fp_time_left * (in_voltage / lower_threshold)

        return fp_time_left

    def _calc_battery_discharge(self):
        """Approximate battery discharge per second based on 
        the runtime model & current wattage draw

        Returns:
            float: discharge per second 
        """

        wattage = self.state.wattage
        fp_estimated_timeleft = self._calc_full_power_time_left(wattage)
        return self.state.battery_max_level / (fp_estimated_timeleft * 60)

    def _increase_transfer_severity(self):
        """Increase severity of the input power event
        (blackout, brownout etc. )
        """

        last_reason = self.state.transfer_reason

        if last_reason == self.state.InputLineFailCause.smallMomentarySag:
            new_reason = self.state.InputLineFailCause.brownout
        elif last_reason == self.state.InputLineFailCause.deepMomentarySag:
            new_reason = self.state.InputLineFailCause.blackout
        else:
            logger.warning(
                "The UPS is not in momentary line fail state: %s", last_reason.name
            )
            return

        self.state.update_transfer_reason(new_reason)

    def _drain_battery(self):
        """When parent is not available -> drain battery 
        """

        battery_level = self.state.battery_level
        old_battery_lvl = -1

        outage = False
        to_adv_percentage = lambda x: int(x * 0.1)

        # keep draining battery while its level remains above 0
        # UPS is on and parent is down
        while (
            battery_level > 0
            and self.state.status
            and self.state.on_battery
            and not self._stop_event.is_set()
        ):

            # calculate new battery level
            battery_level = battery_level - (
                self._calc_battery_discharge() * self._drain_speed_factor
            )

            if to_adv_percentage(battery_level) != to_adv_percentage(old_battery_lvl):
                logger.info("on battery: %s %%", to_adv_percentage(battery_level))

            seconds_on_battery = (dt.now() - self._start_time_battery).seconds

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )
            self.state.update_time_on_battery(seconds_on_battery * 100)

            if seconds_on_battery >= self.state.momentary_event_period and not outage:
                outage = True
                self._increase_transfer_severity()

            old_battery_lvl = battery_level
            self._stop_event.wait(1)

        # kill the thing if still breathing
        if self.state.status and self.state.on_battery:
            self._snmp_agent.stop_agent()
            self.state.publish_power(old_state=1, new_state=0)

    def _charge_battery(self, power_up_on_charge=False):
        """Charge battery when there's upstream power source & battery is not full
                
        Args:
            power_up_on_charge(boolean): indicates if the asset should be powered up
                                         when min charge level is achieved

        """

        battery_level = self.state.battery_level
        old_battery_lvl = -1
        powered = False

        to_adv_percentage = lambda x: int(x * 0.1)

        # keep charging battery while its level is less than max & parent is up
        while (
            battery_level < self.state.battery_max_level
            and not self.state.on_battery
            and not self._stop_event.is_set()
        ):
            # calculate new battery level
            battery_level = battery_level + (
                self._charge_per_second * self._charge_speed_factor
            )

            if to_adv_percentage(battery_level) != to_adv_percentage(old_battery_lvl):
                logger.info("charging battery: %s %%", to_adv_percentage(battery_level))

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )

            # power up on min charge level
            if (not powered and power_up_on_charge) and (
                battery_level > self.state.min_restore_charge_level
            ):
                old_state = self.state.status
                powered = self.power_up()
                self.state.publish_power(old_state, self.state.status)

            old_battery_lvl = battery_level
            self._stop_event.wait(1)

    def _launch_battery_drain(
        self, t_reason=in_state.UPSStateManager.InputLineFailCause.deepMomentarySag
    ):
        """Start a thread that will decrease battery level """

        if self._battery_drain_t and self._battery_drain_t.isAlive():
            logger.warning("Battery drain is already running!")
            self.state.update_transfer_reason(t_reason)
            self._increase_transfer_severity()
            return

        self._start_time_battery = dt.now()

        # update state details
        self.state.update_ups_output_status(
            in_state.UPSStateManager.OutputStatus.onBattery
        )
        self.state.update_transfer_reason(t_reason)

        # wait for other thread to finish
        if self._battery_charge_t:
            self._battery_charge_t.join()

        # launch a thread
        self._battery_drain_t = Thread(
            target=self._drain_battery, name="battery_drain:{}".format(self.key)
        )
        self._battery_drain_t.daemon = True
        self._battery_drain_t.start()

    def _launch_battery_charge(self, power_up_on_charge=False):
        """Start a thread that will charge battery level """

        if self._battery_charge_t and self._battery_charge_t.isAlive():
            logger.warning("Battery is already charging!")
            return

        self.state.update_time_on_battery(0)

        # update state details
        self.state.update_ups_output_status(
            in_state.UPSStateManager.OutputStatus.onLine
        )
        self.state.update_transfer_reason(
            in_state.UPSStateManager.InputLineFailCause.noTransfer
        )

        # wait for battery drain thread to wrap up before charging
        if self._battery_drain_t:
            self._battery_drain_t.join()

        # launch a thread
        self._battery_charge_t = Thread(
            target=self._charge_battery,
            args=(power_up_on_charge,),
            name="battery_charge:{}".format(self.key),
        )
        self._battery_charge_t.daemon = True
        self._battery_charge_t.start()

    @handler("SignalDownEvent")
    def on_signal_down_received(self, event, *args, **kwargs):
        """UPS can be powered down by snmp command"""
        self.state.update_ups_output_status(in_state.UPSStateManager.OutputStatus.off)

        if "graceful" in kwargs and kwargs["graceful"]:
            e_result = self.shut_down()
        else:
            e_result = self.power_off()

        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("PowerButtonOnEvent", "PowerButtonOffEvent")
    def on_power_button_press(self, event, *args, **kwargs):
        """React to power button event by notifying engine of
        state changes associated with it"""

        asset_event = event.get_next_power_event()
        asset_event.calc_load_from_volt()

        if self.state.on_battery and asset_event.state.new:
            asset_event.out_volt.new = 120.0
        elif not asset_event.state.new:
            asset_event.out_volt.old = self.state.output_voltage

        super().set_redis_state_on_btn_press(event, args, kwargs)

        if event.name == "PowerButtonOnEvent" and self.state.on_battery:
            self._launch_battery_drain(t_reason=self.state.transfer_reason)

        return asset_event

    def _get_ups_load_update(self, should_transfer):
        """Get formatted load event result 
        (load update that needs to be propagated up the power stream)
        """

        load = self.state.load
        old_load, new_load = (load, 0) if should_transfer else (0, load)

        # Meaning ups state hasn't changed
        # (it was already on battery or it was already using input power)
        if should_transfer == self.state.on_battery or old_load == new_load:
            return None

        return old_load, new_load

    @handler("ChildLoadUpEvent", "ChildLoadDownEvent")
    def on_child_load_update(self, event, *args, **kwargs):
        """Process child load changes by updating load of the device"""
        # when not on battery, process load as normal
        if not self.state.on_battery:
            return super().on_child_load_update(event, *args, **kwargs)

        # while running on battery, load propagation gets halted
        asset_load_event = event.get_next_load_event(self)
        self._update_load(asset_load_event.load.old + event.load.difference)

        # ensure that load doesn't change for the parent
        asset_load_event.load.new = asset_load_event.load.old
        return asset_load_event

    @handler("InputVoltageUpEvent")
    def on_input_voltage_up(self, event, *args, **kwargs):
        """React to input voltage spike;
        UPS can transfer to battery if in-voltage is too high;
        It can also transfer back to input power if voltage level is
        within the acceptable threshold;
        """
        asset_event = event.get_next_power_event(self)
        asset_event.out_volt.old = self.state.output_voltage
        asset_event.calc_load_from_volt()

        # process voltage, see if tranfer to battery is needed
        should_transfer, reason = self.state.process_voltage(event.in_volt.new)

        upstream_load_change = self._get_ups_load_update(should_transfer)
        if upstream_load_change:
            asset_event.load.old, asset_event.load.new = upstream_load_change

        # transfer back to input power if ups was running on battery
        if not should_transfer and self.state.on_battery:
            battery_level = self.state.battery_level
            self._launch_battery_charge(power_up_on_charge=(not battery_level))
            if battery_level:
                asset_event.state.new = self.state.power_up()

        # if already on battery (& should stay so), stop voltage propagation
        elif self.state.on_battery:
            asset_event.out_volt.new = asset_event.out_volt.old

        # voltage is too high, transfer to battery
        if should_transfer and reason == self.state.InputLineFailCause.highLineVoltage:
            self._launch_battery_drain(reason)
            asset_event.out_volt.new = ISystemEnvironment.wallpower_volt_standard()

        if not math.isclose(asset_event.load.new, 0) and not math.isclose(
            asset_event.load.new, self.state.load
        ):
            self._update_load(self.state.load + asset_event.load.difference)

        return asset_event

    @handler("InputVoltageDownEvent")
    def on_input_voltage_down(self, event, *args, **kwargs):
        """React to input voltage drop;
        UPS can transfer to battery if in-voltage is low or
        it can transfer back to input power if volt dropped from
        too high to acceptable;
        """

        asset_event = event.get_next_power_event(self)
        asset_event.out_volt.old = self.state.output_voltage

        battery_level = self.state.battery_level
        should_transfer, reason = self.state.process_voltage(event.in_volt.new)

        upstream_load_change = self._get_ups_load_update(should_transfer)
        if upstream_load_change:
            asset_event.load.old, asset_event.load.new = upstream_load_change

        high_line_t_reason = self.state.InputLineFailCause.highLineVoltage

        # voltage is low, transfer to battery
        if should_transfer and self.state.battery_level:
            self._launch_battery_drain(reason)
            asset_event.out_volt.new = ISystemEnvironment.wallpower_volt_standard()

        # voltage was too high but is okay now
        elif (
            self.state.transfer_reason == high_line_t_reason
            and reason != high_line_t_reason
        ):
            self._launch_battery_charge(power_up_on_charge=(not battery_level))
        else:
            asset_event.calc_load_from_volt()
            self._update_load(self.state.load + asset_event.load.difference)

        return asset_event

    @property
    def draining_battery(self):
        """Returns true if UPS battery is being drained"""
        return self._battery_drain_t is not None and self._battery_drain_t.isAlive()

    @property
    def charging_battery(self):
        """Returns true if UPS battery is getting re-charged"""
        return self._battery_charge_t is not None and self._battery_charge_t.isAlive()

    @property
    def charge_speed_factor(self):
        """Estimated charge/sec will be multiplied by this value"""
        return self._charge_speed_factor

    @charge_speed_factor.setter
    def charge_speed_factor(self, speed):
        self._charge_speed_factor = speed

    @property
    def drain_speed_factor(self):
        """Estimated drain/sec will be multiplied by this value"""
        return self._drain_speed_factor

    @drain_speed_factor.setter
    def drain_speed_factor(self, speed):
        self._drain_speed_factor = speed

    def _update_load(self, new_load):
        """Ups needs to update runtime left for battery when load is updated"""
        upd_result = self.state.update_load(new_load)
        # re-calculate time left based on updated load
        if not math.isclose(self.state.wattage, 0):
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )
        return upd_result

    def __str__(self):
        return super().__str__() + (
            " [charge-state]\n"
            "   - thread active: {0.charging_battery}\n"
            "   - speed factor: {0.charge_speed_factor}\n"
            " [drain-state]\n"
            "   - thread active: {0.draining_battery}\n"
            "   - speed factor: {0.drain_speed_factor}\n"
        ).format(self)

    def stop(self, code=None):
        self._snmp_agent.stop_agent()
        self._stop_event.set()

        for thread in [self._battery_charge_t, self._battery_drain_t]:
            if thread is not None and thread.isAlive():
                thread.join()

        super().stop(code)
