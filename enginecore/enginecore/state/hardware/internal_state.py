"""Contains extended versions of State Managers located in api module;
Internal States are meant to be manipulated by 
the hardware assets (server_asset, ups_asset etc.)
So they expose extra functionality on top of the api components
"""
import json
from enum import Enum

import pysnmp.proto.rfc1902 as snmp_data_types
from enginecore.model.graph_reference import GraphReference

from enginecore.state.redis_channels import RedisChannels
import enginecore.state.api as state_api

from enginecore.tools.utils import convert_voltage_to_high_prec


class StateManager(state_api.IStateManager, state_api.ISystemEnvironment):
    """Exposes private logic to assets"""

    def update_agent(self, pid):
        """Set agent PID"""
        StateManager.get_store().set(self.redis_key + ":agent", pid)

    def update_input_voltage(self, voltage):
        """Update asset input voltage"""
        super()._update_input_voltage(voltage)

    def reset_boot_time(self):
        """Reset the boot time to now"""
        super()._reset_boot_time()

    def publish_power(self, old_state, new_state):
        """Publish state changes (expose method to the assets) """
        super()._publish_power(old_state, new_state)

    def _set_state_on(self):
        """Set redis state to 1 without publishing power to the engine"""
        self.set_redis_asset_state(1)

    def _set_state_off(self):
        """Set redis state to 0 without publishing power to the engine"""
        self.set_redis_asset_state(0)

    def set_redis_asset_state(self, state):
        """Update redis value of the asset power status"""
        super()._set_redis_asset_state(state)

    def update_load(self, load):
        """Update load """
        super()._update_load(load)


class UPSStateManager(state_api.IUPSStateManager, StateManager):
    """Handles UPS state logic """

    def update_temperature(self, temp):
        """Set battery temperature of the device"""
        oid_value = (temp + state_api.ISystemEnvironment.get_ambient()) * 10
        self._update_oid_by_name(
            "HighPrecBatteryTemperature", snmp_data_types.Gauge32(oid_value)
        )

    def update_battery(self, charge_level):
        """Updates battery level, checks for the charge level
        being in valid range, sets battery-related OIDs
        and publishes changes;

        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """
        charge_level = max(charge_level, 0)
        charge_level = min(charge_level, self._max_battery_level)

        old_charge_level = self.battery_level
        self._update_battery(charge_level)
        self._update_battery_oids(charge_level, self.battery_level)

        # notify state listener that battery has changed
        self._publish_battery(old_charge_level, charge_level)

    def update_load(self, load):
        """Update any load state associated with the device in the redis db 
        
        Args:
            load(float): New load in amps
        """
        super().update_load(load)
        if "outputPowerCapacity" in self._asset_info and load >= 0:
            self._update_load_perc_oids(load)
            self._update_current_oids(load)

    def update_time_on_battery(self, timeticks):
        """Update OIDs associated with UPS time on battery
        
        Args:
            timeticks(int): time-on battery (seconds*100)
        """
        self._update_oid_by_name("TimeOnBattery", snmp_data_types.TimeTicks(timeticks))

    def update_time_left(self, timeticks):
        """Update OIDs associated with UPS runtime
        (estimation of how long UPS will be operating)
        
        Args:
            timeticks(int): time left
        """
        self._update_oid_by_name(
            "BatteryRunTimeRemaining", snmp_data_types.TimeTicks(timeticks)
        )

    def update_ups_output_status(self, status):
        """Status for output -- either on, off or running on battery
        Args:
            status(OutputStatus): new output status
        """
        self._update_oid_by_name("BasicOutputStatus", status.name, use_spec=True)

    def update_transfer_reason(self, status):
        """Update UPS transfer reason;
        UPS can switch its mode to 'on battery' for multiple reasons
        (e.g. Voltage drop, upstream power failure etc.)
        Args:
            status(InputLineFailCause): new transfer cause
        """
        self._update_oid_by_name("InputLineFailCause", status.name, use_spec=True)

    def _update_current_oids(self, load):
        """Update OIDs associated with UPS Output - Current in AMPs
        
        Args:
            load(float): new load in AMPs
        """
        oid_adv = self.get_oid_by_name("AdvOutputCurrent")
        oid_hp = self.get_oid_by_name("HighPrecOutputCurrent")

        if oid_adv:
            self._update_oid_value(oid_adv, snmp_data_types.Gauge32(load))
        if oid_hp:
            self._update_oid_value(oid_hp, snmp_data_types.Gauge32(load * 10))

    def _update_load_perc_oids(self, load):
        """Update OIDs associated with UPS Output - % of the power capacity
        
        Args:
            load(float): new load in AMPs
        """

        oid_adv = self.get_oid_by_name("AdvOutputLoad")
        oid_hp = self.get_oid_by_name("HighPrecOutputLoad")
        value_hp = abs(
            (1000 * (load * state_api.ISystemEnvironment.get_voltage()))
            / self.output_capacity
        )

        if oid_adv:
            self._update_oid_value(oid_adv, snmp_data_types.Gauge32(value_hp / 10))
        if oid_hp:
            self._update_oid_value(oid_hp, snmp_data_types.Gauge32(value_hp))

    def _update_battery_oids(self, charge_level, old_level):
        """Update OIDs associated with UPS Battery
        
        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """

        # 100%
        oid_adv = self.get_oid_by_name("AdvBatteryCapacity")
        oid_hp = self.get_oid_by_name("HighPrecBatteryCapacity")
        oid_basic = self.get_oid_by_name("BasicBatteryStatus")

        if oid_adv:
            self._update_oid_value(oid_adv, snmp_data_types.Gauge32(charge_level / 10))
        if oid_hp:
            self._update_oid_value(oid_hp, snmp_data_types.Gauge32(charge_level))

        if not oid_basic:
            return

        if charge_level <= 100:
            low_bat_value = oid_basic.specs["batteryLow"]
            self._update_oid_value(oid_basic, snmp_data_types.Integer32(low_bat_value))
        elif old_level <= 100 < charge_level:
            norm_bat_value = oid_basic.specs["batteryNormal"]
            self._update_oid_value(oid_basic, snmp_data_types.Integer32(norm_bat_value))

    def process_voltage(self, voltage):
        """Update oids associated with UPS voltage
        Args:
            voltage: new voltage value
        Returns: 
            tuple: true if transfer to battery is needed, transfer reason
                   (see state.api.ups.UPS.InputLineFailCause)
        Raises:
            ValueError: if UPS has no voltage OIDs defined
                        or transfer reason cannot be determined
        """

        oid_in_adv = self.get_oid_by_name("AdvInputLineVoltage")
        oid_in_high_prec = self.get_oid_by_name("HighPrecInputLineVoltage")
        oid_out_adv = self.get_oid_by_name("AdvOutputVoltage")
        oid_out_high_prec = self.get_oid_by_name("HighPrecOutputVoltage")

        if (
            not oid_in_adv
            or not oid_in_high_prec
            or not oid_out_adv
            or not oid_out_high_prec
        ):
            raise ValueError("UPS doesn't support voltage OIDs!")

        oid_voltage_value = snmp_data_types.Gauge32(int(voltage))

        # update input OID parameter
        self._update_oid_value(oid_in_adv, oid_voltage_value)
        self._update_oid_value(
            oid_in_high_prec, convert_voltage_to_high_prec(oid_voltage_value)
        )

        # retrieve thresholds:
        oid_high_th = self.get_oid_by_name("AdvConfigHighTransferVolt")
        oid_low_th = self.get_oid_by_name("AdvConfigLowTransferVolt")

        # update output OID value if thresholds are not supported
        if not oid_high_th or not oid_low_th:
            self._update_oid_value(oid_out_adv, oid_voltage_value)
            self._update_oid_value(
                oid_out_high_prec, convert_voltage_to_high_prec(oid_voltage_value)
            )
            return False, None

        high_th = int(self.get_oid_value(oid_high_th))
        low_th = int(self.get_oid_value(oid_low_th))

        # new voltage value is within the threasholds
        if low_th < voltage < high_th:
            self._update_oid_value(oid_out_adv, oid_voltage_value)
            self._update_oid_value(
                oid_out_high_prec, convert_voltage_to_high_prec(oid_voltage_value)
            )
            return False, None

        # new voltage should cause line transfer:
        r_out_threshold = self.rated_output_threshold

        if 0 <= voltage < r_out_threshold:
            transfer_reason = self.InputLineFailCause.deepMomentarySag
        elif r_out_threshold <= voltage <= low_th:
            transfer_reason = self.InputLineFailCause.smallMomentarySag
        elif voltage >= high_th:
            transfer_reason = self.InputLineFailCause.highLineVoltage
        else:
            raise ValueError("Unknow transfer reason!")

        return True, transfer_reason

    def _publish_battery(self, old_battery_lvl, new_battery_lvl):
        """Publish battery update
        Args:
            old_battery_lvl(int): range 0-1000 (what battery level used to be)
            new_battery_lvl(int): range 0-1000 (new battery charge level)
        """
        StateManager.get_store().publish(
            RedisChannels.battery_update_channel,
            json.dumps(
                {
                    "key": self.key,
                    "old_battery": old_battery_lvl,
                    "new_battery": new_battery_lvl,
                }
            ),
        )


class PDUStateManager(state_api.IPDUStateManager, StateManager):
    """Handles state logic for PDU asset """

    def _update_current(self, load):
        """Update OID associated with the current amp value """
        oid = self.get_oid_by_name("AmpOnPhase")

        if not oid:
            return

        self._update_oid_value(oid, snmp_data_types.Gauge32(max(load, 0) * 10))

    def _update_wattage(self, wattage):
        """Update OID associated with the current wattage draw """
        oid = self.get_oid_by_name("WattageDraw")

        if not oid:
            return

        self._update_oid_value(oid, snmp_data_types.Integer32(max(wattage, 0)))

    def update_load(self, load):
        """Update any load state associated with the device in the redis db 
        
        Args:
            load(float): New load in amps
        """
        super(PDUStateManager, self).update_load(load)
        self._update_current(load)
        self._update_wattage(load * state_api.ISystemEnvironment.get_voltage())


class OutletStateManager(state_api.IOutletStateManager, StateManager):
    """Handles state logic for outlet asset """

    class OutletState(Enum):
        """Outlet States (oid) """

        switchOff = 1
        switchOn = 2

    def get_oid_value_by_name(self, oid_name):
        """Get value under object id name"""
        with self._graph_ref.get_session() as session:
            oid, parent_key = GraphReference.get_component_oid_by_name(
                session, self.key, oid_name
            )
        if oid:
            oid = "{}.{}".format(oid, str(self.key)[-1])
            return int(self.get_oid_value(oid, key=parent_key))

        return 0

    def set_parent_oid_states(self, state):
        """Bulk-set parent oid values 
        
        Args:
            state(OutletState): new parent(s) state
        """
        with self._graph_ref.get_session() as session:
            _, oids = GraphReference.get_parent_keys(session, self._asset_key)

        oid_keys = oids.keys()
        parents_new_states = {}
        parent_values = StateManager.get_store().mget(oid_keys)

        for rkey, rvalue in zip(oid_keys, parent_values):
            #  datatype -> {} | {} <- value
            parents_new_states[rkey] = "{}|{}".format(
                rvalue.split(b"|")[0].decode(), oids[rkey][state.name]
            )

        StateManager.get_store().mset(parents_new_states)

    # TODO: move to interface
    def get_config_off_delay(self):
        return self.get_oid_value_by_name("OutletConfigPowerOffTime")

    def get_config_on_delay(self):
        return self.get_oid_value_by_name("OutletConfigPowerOnTime")


class StaticDeviceStateManager(state_api.IStaticDeviceStateManager, StateManager):
    """Dummy Device that doesn't do much except drawing power """

    pass


class ServerStateManager(state_api.IServerStateManager, StaticDeviceStateManager):
    """Server state manager offers control over VM's state """


class BMCServerStateManager(state_api.IBMCServerStateManager, ServerStateManager):
    """Manage Server with BMC """

    def update_cpu_load(self, value):
        """Set CPU load"""
        StateManager.get_store().set(self.redis_key + ":cpu_load", str(int(value)))

    def update_storage_temperature(self, old_ambient, new_ambient):

        with self._graph_ref.get_session() as db_s:

            hd_elements = GraphReference.get_all_hd_thermal_elements(db_s, self.key)

            for hd_e in hd_elements:

                if "DID" in hd_e["component"]:
                    target_attr = "DID"
                    target_value = hd_e["component"]["DID"]
                    target_type = "PhysicalDrive"
                else:
                    target_attr = "serialNumber"
                    target_value = '"{}"'.format(hd_e["component"]["serialNumber"])
                    target_type = "CacheVault"

                updated, new_temp = GraphReference.add_to_hd_component_temperature(
                    db_s,
                    target={
                        "server_key": self.key,
                        "controller": hd_e["controller"]["controllerNum"],
                        "attribute": target_attr,
                        "value": target_value,
                        "hd_type": target_type,
                    },
                    temp_change=new_ambient - old_ambient,
                    limit={"lower": new_ambient, "upper": None},
                )


class PSUStateManager(state_api.IPSUStateManager, StateManager):
    """Power Supply"""

    def __init__(self, asset_info):
        StateManager.__init__(self, asset_info)
        self._psu_number = int(repr(asset_info["key"])[-1])

    def get_psu_sensor_names(self):
        """Find out BMC-specific psu keys (voltage, status etc.)
        Returns:
            dict: key value pairs of sensor type / sensor name for the psu
        """
        with self._graph_ref.get_session() as db_s:
            return GraphReference.get_psu_sensor_names(db_s, self.key, self._psu_number)
