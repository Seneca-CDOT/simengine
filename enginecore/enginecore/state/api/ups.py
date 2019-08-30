"""UPS asset interface """
import time
import json
from enum import Enum

from enginecore.state.redis_channels import RedisChannels
from enginecore.state.api.state import IStateManager, ISystemEnvironment
from enginecore.state.api.snmp_state import ISnmpDeviceStateManager
from enginecore.tools.randomizer import Randomizer


@Randomizer.register
class IUPSStateManager(ISnmpDeviceStateManager):
    """Handles UPS state logic """

    class OutputStatus(Enum):
        """UPS output status """

        onLine = 1
        onBattery = 2
        off = 3

    class InputLineFailCause(Enum):
        """Reason for the occurrence of the last transfer to UPS
        The variable is set to:
            - noTransfer(1) -- if there is no transfer yet.

            - highLineVoltage(2) -- if the transfer to battery is caused
            by an over voltage greater than the high transfer voltage.
            
            - brownout(3) -- if the duration of the outage is greater than
            five seconds and the line voltage is between 40% of the
            rated output voltage and the low transfer voltage.
            
            - blackout(4) -- if the duration of the outage is greater than five
            seconds and the line voltage is between 40% of the rated
            output voltage and ground.
            
            - smallMomentarySag(5) -- if the duration of the outage is less
            than five seconds and the line voltage is between 40% of the
            rated output voltage and the low transfer voltage.
            
            - deepMomentarySag(6) -- if the duration of the outage is less
            than five seconds and the line voltage is between 40% of the
            rated output voltage and ground.  The variable is set to
            
            - smallMomentarySpike(7) -- if the line failure is caused by a
            rate of change of input voltage less than ten volts per cycle.
            
            - largeMomentarySpike(8) -- if the line failure is caused by
            a rate of change of input voltage greater than ten volts per cycle.
            
            - selfTest(9) -- if the UPS was commanded to do a self test.
            
            - rateOfVoltageChange(10) -- if the failure is due to the rate of change of
            the line voltage.
        """

        noTransfer = 1
        highLineVoltage = 2
        brownout = 3
        blackout = 4
        smallMomentarySag = 5
        deepMomentarySag = 6
        smallMomentarySpike = 7
        largeMomentarySpike = 8
        selfTest = 9
        rateOfVoltageChange = 10

    def __init__(self, asset_info):
        super().__init__(asset_info)
        self._max_battery_level = 1000  #%

    def _update_battery_process_speed(self, process_channel, factor):
        """Speed up/slow down battery related process"""
        IStateManager.get_store().publish(
            process_channel, json.dumps({"key": self.key, "factor": factor})
        )

    def _reset_power_off_oid(self):
        """Reset upsAdvControlUpsOff to 1 """
        # TODO different vendors may assign other values (not 1)
        self._update_oid_by_name("PowerOff", 1)

    @property
    def battery_level(self):
        """Get current level (high-precision)"""
        battery_lvl = IStateManager.get_store().get(self.redis_key + ":battery")
        return int(battery_lvl.decode()) if battery_lvl else 0

    def _update_battery(self, charge_level):
        """Battery level setter
        Args:
            charge_level(int): new charge level in high-precision format (0-1000)
        """
        # make sure new charge level is within acceptable range
        charge_level = max(charge_level, 0)
        charge_level = min(charge_level, self._max_battery_level)

        IStateManager.get_store().set(self.redis_key + ":battery", int(charge_level))

    @property
    def battery_max_level(self):
        """Max battery level"""
        return self._max_battery_level

    @property
    def on_battery(self):
        """Indicates if UPS is powered by battery at the moment"""
        return self.transfer_reason != self.InputLineFailCause.noTransfer

    @property
    def transfer_reason(self):
        """Retrieve last transfer reason (why switched from input power to battery)
        Returns:
            InputLineFailCause: last transfer cause
        """
        oid_t_reason = self.get_oid_by_name("InputLineFailCause")
        return self.InputLineFailCause(int(self.get_oid_value(oid_t_reason)))

    @property
    def output_voltage(self):
        if self.on_battery:
            return self.status * ISystemEnvironment.wallpower_volt_standard()

        return self.input_voltage

    @property
    def wattage(self):
        return self.load * self._asset_info["powerSource"]

    @property
    def idle_ups_amp(self):
        """How much a UPS draws"""
        return self._asset_info["powerConsumption"] / self._asset_info["powerSource"]

    @property
    def min_restore_charge_level(self):
        """min level of battery charge before UPS can be powered on"""
        return self._asset_info["minPowerOnBatteryLevel"]

    @property
    def full_recharge_time(self):
        """hours taken to recharge the battery when it's completely depleted"""
        return self._asset_info["fullRechargeTime"]

    @property
    def output_capacity(self):
        """UPS rated capacity"""
        return self._asset_info["outputPowerCapacity"]

    @property
    def rated_output_threshold(self):
        """Threshold derived from the rated output used to determine
        if transfer to battery is needed (see IUPSStateManager.InputLineFailCause)
        """
        ro_percent = 0.4

        if "ratedOutputPercentage" in self._asset_info:
            ro_percent = self._asset_info["ratedOutputPercentage"]

        in_voltage_oid = self.get_oid_by_name("AdvConfigRatedOutputVoltage")
        return ro_percent * int(self.get_oid_value(in_voltage_oid))

    @property
    def momentary_event_period(self):
        """Power sag/spike time period. Momentary event
        (see IUPSStateManager.InputLineFailCause) happens
        before transfer reason is assigned an elevated severity.

        Returns:
            int: time period in seconds
        """
        t_period = 5  # seconds

        if "momentaryEventTime" in self._asset_info:
            t_period = self._asset_info["momentaryEventTime"]

        return t_period

    @Randomizer.randomize_method()
    def power_off(self):
        powered = super().power_off()
        if not powered:
            self._update_load(self.load - self.power_usage)

    @Randomizer.randomize_method()
    def shut_down(self):
        time.sleep(self.get_config_off_delay())
        powered = super().shut_down()
        if not powered:
            self._update_load(self.load - self.power_usage)

        return powered

    @Randomizer.randomize_method()
    def power_up(self):

        powered = self.status

        if self.battery_level and not self.status:
            self._sleep_powerup()
            time.sleep(self.get_config_on_delay())
            # update machine start time & turn on
            self._reset_boot_time()
            self._set_state_on()

            self._reset_power_off_oid()
            self.enable_net_interface()
            self._update_load(self.power_usage)

            powered = 1

        return powered

    def get_config_off_delay(self):
        """Delay for power-off operation 
        (unlike 'hardware'-determined delay, this value can be configured by the user)
        """
        oid = self.get_oid_by_name("AdvConfigShutoffDelay")
        return int(self.get_oid_value(oid))

    def get_config_on_delay(self):
        """Power-on delay
        (unlike 'hardware'-determined delay, this value can be configured by the user)
        """
        oid = self.get_oid_by_name("AdvConfigReturnDelay")
        return int(self.get_oid_value(oid))

    def set_drain_speed_factor(self, factor):
        """Speed up/slow down UPS battery draining process
        (note that this will produce 'unreal' behaviour)
        """
        self._update_battery_process_speed(
            RedisChannels.battery_conf_drain_channel, factor
        )

    def set_charge_speed_factor(self, factor):
        """Speed up/slow down UPS battery charging
        (note that this will produce 'unreal' behaviour)
        """
        self._update_battery_process_speed(
            RedisChannels.battery_conf_charge_channel, factor
        )

    def __str__(self):
        return super(IUPSStateManager, self).__str__() + (
            " - On Battery: {0.on_battery}\n"
            " - Last Transfer Reason: {0.transfer_reason}\n"
            " - Battery Level: {0.battery_level}\n"
        ).format(self)
