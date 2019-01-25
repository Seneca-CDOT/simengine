import time
import os
import tempfile
import json
from enum import Enum

import redis
import libvirt
import pysnmp.proto.rfc1902 as snmp_data_types
from enginecore.model.graph_reference import GraphReference
import enginecore.model.system_modeler as sys_modeler

from enginecore.state.utils import format_as_redis_key
from enginecore.state.redis_channels import RedisChannels
from enginecore.state.api.state import IStateManager




class IUPSStateManager(IStateManager):
    """Handles UPS state logic """


    class OutputStatus(Enum):
        """UPS output status """
        onLine = 1
        onBattery = 2
        off = 3
    

    class InputLineFailCause(Enum):
        """Reason for the occurrence of the last transfer to UPS """
        noTransfer = 1
        blackout = 2
        deepMomentarySag = 3


    def __init__(self, asset_info):
        super().__init__(asset_info)
        self._max_battery_level = 1000#%


    @property
    def battery_level(self):
        """Get current level (high-precision)"""
        return int(IStateManager.get_store().get(self.redis_key + ":battery").decode())


    @property
    def battery_max_level(self):
        """Max battery level"""
        return self._max_battery_level


    @property
    def wattage(self):
        return (self.load + self.idle_ups_amp) * self._asset_info['powerSource']


    @property
    def idle_ups_amp(self):
        """How much a UPS draws"""
        return self._asset_info['powerConsumption'] / self._asset_info['powerSource']


    @property
    def min_restore_charge_level(self):
        """min level of battery charge before UPS can be powered on"""
        return self._asset_info['minPowerOnBatteryLevel']


    @property
    def full_recharge_time(self):
        """hours taken to recharge the battery when it's completely depleted"""
        return self._asset_info['fullRechargeTime']


    @property
    def output_capacity(self):
        """UPS rated capacity"""
        return self._asset_info['outputPowerCapacity']


    def shut_down(self):
        time.sleep(self.get_config_off_delay())
        powered = super().shut_down()
        return powered


    def power_up(self):
        print("Powering up {}".format(self._asset_key))

        if self.battery_level and not self.status:
            self._sleep_powerup()
            time.sleep(self.get_config_on_delay())
            # udpate machine start time & turn on
            self._reset_boot_time()
            self._set_state_on()
        
        powered = self.status
        if powered:
            self._reset_power_off_oid()

        return powered


    def get_config_off_delay(self):
        """Delay for power-off operation 
        (unlike 'hardware'-determined delay, this value can be configured by the user)
        """
        with self._graph_ref.get_session() as db_s:
            oid, _, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvConfigShutoffDelay')
            return int(self._get_oid_value(oid, key=self._asset_key))


    def get_config_on_delay(self):
        """Power-on delay
        (unlike 'hardware'-determined delay, this value can be configured by the user)
        """

        with self._graph_ref.get_session() as db_s:
            oid, _, _ = GraphReference.get_asset_oid_by_name(db_s, int(self._asset_key), 'AdvConfigReturnDelay')
            return int(self._get_oid_value(oid, key=self._asset_key))


    def _update_battery_process_speed(self, process_channel, factor):
        """Speed up/slow down battery related process"""
        rkey = "{}|{}".format(self.redis_key, factor)
        IStateManager.get_store().publish(process_channel, rkey)


    def set_drain_speed_factor(self, factor):
        """Speed up/slow down UPS battery draining process
        (note that this will produce 'unreal' behaviour)
        """
        self._update_battery_process_speed(RedisChannels.battery_conf_drain_channel, factor)
    

    def set_charge_speed_factor(self, factor):
        """Speed up/slow down UPS battery charging
        (note that this will produce 'unreal' behaviour)
        """
        self._update_battery_process_speed(RedisChannels.battery_conf_charge_channel, factor)


    def _reset_power_off_oid(self):
        """Reset upsAdvControlUpsOff to 1 """
        # TODO different vendors may assign other values (not 1)
        self._update_oid_by_name('PowerOff', snmp_data_types.Integer, 1)


