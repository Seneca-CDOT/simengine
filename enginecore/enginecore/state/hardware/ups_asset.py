"""Event handler for UPS (Uninterrupted power supply)
UPS asset supports snmp interface & manages power source for the output power stream
For example, it switches to battery if upstream power is offline or voltage is too low
"""
# **due to circuit callback signature
# pylint: disable=W0613

import logging
import json
import time
from datetime import datetime as dt

from threading import Thread
from circuits import handler
import enginecore.state.hardware.internal_state as in_state
from enginecore.state.hardware.asset import Asset
from enginecore.state.hardware.snmp_asset import SNMPSim

from enginecore.state.hardware.asset_definition import register_asset


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
        Asset.__init__(self, UPS.StateManagerCls(asset_info))
        SNMPSim.__init__(
            self, asset_info["key"], asset_info["host"], asset_info["port"]
        )

        self.state.update_agent(self._snmp_agent.pid)

        # Store known { wattage: time_remaining } key/value pairs (runtime graph)
        self._runtime_details = json.loads(asset_info["runtime"])

        # Track upstream power availability
        self._parent_up = True
        self._charge_speed_factor = 1
        self._drain_speed_factor = 1

        # Threads responsible for battery charge/discharge
        self._battery_drain_t = None
        self._battery_charge_t = None

        self._start_time_battery = None

        # set battery level to max
        self.state.update_battery(self.state.battery_max_level)

        # get charge per second using full recharge time (hrs)
        self._charge_per_second = self.state.battery_max_level / (
            self.state.full_recharge_time * 60 * 60
        )

        # set temp on start
        self._state.update_temperature(7)
        logging.info(self._snmp_agent)

    def _cacl_time_left(self, wattage):
        """Approximate runtime estimation based on current battery level"""
        return (
            self._calc_full_power_time_left(wattage) * self.state.battery_level
        ) / self.state.battery_max_level

    def _calc_full_power_time_left(self, wattage):
        """Approximate runtime estimation for the fully-charged battery"""
        close_wattage = min(self._runtime_details, key=lambda x: abs(int(x) - wattage))
        close_timeleft = self._runtime_details[close_wattage]
        return (close_timeleft * int(close_wattage)) / wattage  # inverse proportion

    def _calc_battery_discharge(self):
        """Approximate battery discharge per second based on the runtime model & current wattage draw

        Returns:
            float: discharge per second 
        """
        # return 100
        wattage = self.state.wattage
        fp_estimated_timeleft = self._calc_full_power_time_left(wattage)
        return self.state.battery_max_level / (fp_estimated_timeleft * 60)

    def _drain_battery(self, parent_up):
        """When parent is not available -> drain battery 
        
        Args:
            parent_up(callable): indicates if the upstream power is available
        """

        battery_level = self.state.battery_level
        blackout = False

        # keep draining battery while its level remains above 0, UPS is on and parent is down
        while battery_level > 0 and self.state.status and not parent_up():

            # calculate new battery level
            battery_level = battery_level - (
                self._calc_battery_discharge() * self._drain_speed_factor
            )
            seconds_on_battery = (dt.now() - self._start_time_battery).seconds

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )
            self.state.update_time_on_battery(seconds_on_battery * 100)

            if seconds_on_battery > 5 and not blackout:
                blackout = True
                self.state.update_transfer_reason(
                    in_state.UPSStateManager.InputLineFailCause.blackout
                )

            time.sleep(1)

        # kill the thing if still breathing
        if self.state.status and not parent_up():
            self._snmp_agent.stop_agent()
            self.state.power_off()
            self.state.publish_power()

    def _charge_battery(self, parent_up, power_up_on_charge=False):
        """Charge battery when there's upstream power source & battery is not full
                
        Args:
            parent_up(callable): indicates if the upstream power is available
            power_up_on_charge(boolean): indicates if the asset should be powered up when min charge level is achieved

        """

        battery_level = self.state.battery_level
        powered = False

        # keep charging battery while its level is less than max & parent is up
        while battery_level < self.state.battery_max_level and parent_up():

            # calculate new battery level
            battery_level = battery_level + (
                self._charge_per_second * self._charge_speed_factor
            )

            # update state details
            self.state.update_battery(battery_level)
            self.state.update_time_left(
                self._cacl_time_left(self.state.wattage) * 60 * 100
            )

            # power up on min charge level
            if (not powered and power_up_on_charge) and (
                battery_level > self.state.min_restore_charge_level
            ):
                e_result = self.power_up()
                powered = e_result.new_state
                self.state.publish_power()

            time.sleep(1)

    def _launch_battery_drain(self):
        """Start a thread that will decrease battery level """

        self._start_time_battery = dt.now()

        # update state details
        self.state.update_ups_output_status(
            in_state.UPSStateManager.OutputStatus.onBattery
        )
        self.state.update_transfer_reason(
            in_state.UPSStateManager.InputLineFailCause.deepMomentarySag
        )

        # launch a thread
        self._battery_drain_t = Thread(
            target=self._drain_battery,
            args=(lambda: self._parent_up,),
            name="battery_drain:{}".format(self.key),
        )
        self._battery_drain_t.daemon = True
        self._battery_drain_t.start()

    def _launch_battery_charge(self, power_up_on_charge=False):
        """Start a thread that will charge battery level """
        self.state.update_time_on_battery(0)

        # update state details
        self.state.update_ups_output_status(
            in_state.UPSStateManager.OutputStatus.onLine
        )
        self.state.update_transfer_reason(
            in_state.UPSStateManager.InputLineFailCause.noTransfer
        )

        # launch a thread
        self._battery_charge_t = Thread(
            target=self._charge_battery,
            args=(lambda: self._parent_up, power_up_on_charge),
            name="battery_charge:{}".format(self.key),
        )
        self._battery_charge_t.daemon = True
        self._battery_charge_t.start()

    ##### React to any events of the connected components #####
    @handler("ParentAssetPowerDown")
    def on_parent_asset_power_down(self, event, *args, **kwargs):
        """Upstream power was lost"""

        self._parent_up = False

        # If battery is still alive -> keep UPS up
        if self.state.battery_level:
            self._launch_battery_drain()
            event.success = False
            return

        # Battery is dead
        self.state.update_ups_output_status(in_state.UPSStateManager.OutputStatus.off)

        e_result = self.power_off()
        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("SignalDown")
    def on_signal_down_received(self, event, *args, **kwargs):
        """UPS can be powered down by snmp command"""
        self.state.update_ups_output_status(in_state.UPSStateManager.OutputStatus.off)

        if "graceful" in kwargs and kwargs["graceful"]:
            e_result = self.shut_down()
        else:
            e_result = self.power_off()

        event.success = e_result.new_state != e_result.old_state

        return e_result

    @handler("ButtonPowerUpPressed")
    def on_ups_signal_up(self):
        if self._parent_up:
            self._launch_battery_charge()
        else:
            self._launch_battery_drain()

    @handler("ParentAssetPowerUp")
    def on_power_up_request_received(self, event, *args, **kwargs):

        self._parent_up = True
        battery_level = self.state.battery_level
        self._launch_battery_charge(power_up_on_charge=(not battery_level))

        if battery_level:
            e_result = self.power_up()
            event.success = e_result.new_state != e_result.old_state

            return e_result

        event.success = False
        return None

    @handler("AmbientDecreased", "AmbientIncreased")
    def on_ambient_updated(self, event, *args, **kwargs):
        self._state.update_temperature(7)

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

    def _update_load(self, load_change, arithmetic_op, msg=""):
        upd_result = super()._update_load(load_change, arithmetic_op, msg)
        # re-calculate time left based on updated load
        self.state.update_time_left(self._cacl_time_left(self.state.wattage) * 60 * 100)
        return upd_result
