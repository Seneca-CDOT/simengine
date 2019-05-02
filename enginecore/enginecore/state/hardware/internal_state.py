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


class StateManager(state_api.IStateManager, state_api.ISystemEnvironment):
    def update_agent(self, pid):
        """Set agent PID"""
        StateManager.get_store().set(self.redis_key + ":agent", pid)

    def update_load(self, load):
        """Update load """
        super()._update_load(load)

    def reset_boot_time(self):
        """Reset the boot time to now"""
        super()._reset_boot_time()

    def publish_power(self):
        """Publish state changes (expose method to the assets) """
        super()._publish_power()

    def _set_redis_asset_state(self, state):
        """Update redis value of the asset power status"""
        super()._set_redis_asset_state(state, publish=False)


class UPSStateManager(state_api.IUPSStateManager, StateManager):
    """Handles UPS state logic """

    def update_temperature(self, temp):
        """Set battery temperature of the device"""
        oid_value = (temp + state_api.ISystemEnvironment.get_ambient()) * 10
        self._update_oid_by_name(
            "HighPrecBatteryTemperature", snmp_data_types.Gauge32, oid_value
        )

    def update_battery(self, charge_level):
        """Updates battery level, checks for the charge level
        being in valid range, sets battery-related OIDs
        and publishes changes;

        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """
        # make sure new charge level is within acceptable range
        charge_level = max(charge_level, 0)
        charge_level = min(charge_level, self._max_battery_level)

        StateManager.get_store().set(self.redis_key + ":battery", int(charge_level))
        self._update_battery_oids(charge_level, self.battery_level)
        self._publish_battery()

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
        self._update_oid_by_name("TimeOnBattery", snmp_data_types.TimeTicks, timeticks)

    def update_time_left(self, timeticks):
        """Update OIDs associated with UPS runtime
        (estimation of how long UPS will be operating)
        
        Args:
            timeticks(int): time left
        """
        self._update_oid_by_name(
            "BatteryRunTimeRemaining", snmp_data_types.TimeTicks, timeticks
        )

    def update_ups_output_status(self, status):
        """Status for output -- either on, off or running on battery
        Args:
            status(OutputStatus): new output status
        """
        self._update_oid_by_name(
            "BasicOutputStatus", snmp_data_types.Integer, status.name, use_spec=True
        )

    def update_transfer_reason(self, status):
        """Update UPS transfer reason;
        UPS can switch its mode to 'on battery' for multiple reasons
        (e.g. Voltage drop, upstream power failure etc.)
        Args:
            status(InputLineFailCause): new transfer cause
        """
        self._update_oid_by_name(
            "InputLineFailCause", snmp_data_types.Integer, status.name, use_spec=True
        )

    def _update_current_oids(self, load):
        """Update OIDs associated with UPS Output - Current in AMPs
        
        Args:
            load(float): new load in AMPs
        """
        oid_adv, dt_adv, _ = self.get_asset_oid_by_name("AdvOutputCurrent")
        oid_hp, dt_hp, _ = self.get_asset_oid_by_name("HighPrecOutputCurrent")

        if oid_adv:
            self._update_oid_value(oid_adv, dt_adv, snmp_data_types.Gauge32(load))
        if oid_hp:
            self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(load * 10))

    # TODO: refactor both _update_load_perc_oids & _update_battery_oids, functions seem quite similair
    def _update_load_perc_oids(self, load):
        """Update OIDs associated with UPS Output - % of the power capacity
        
        Args:
            load(float): new load in AMPs
        """

        oid_adv, dt_adv, _ = self.get_asset_oid_by_name("AdvOutputLoad")
        oid_hp, dt_hp, _ = self.get_asset_oid_by_name("HighPrecOutputLoad")
        value_hp = abs(
            (1000 * (load * state_api.ISystemEnvironment.get_voltage()))
            / self.output_capacity
        )

        if oid_adv:
            self._update_oid_value(
                oid_adv, dt_adv, snmp_data_types.Gauge32(value_hp / 10)
            )
        if oid_hp:
            self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(value_hp))

    def _update_battery_oids(self, charge_level, old_level):
        """Update OIDs associated with UPS Battery
        
        Args:
            charge_level(int): new battery level (between 0 & 1000)
        """

        # 100%
        oid_adv, dt_adv, _ = self.get_asset_oid_by_name("AdvBatteryCapacity")
        oid_hp, dt_hp, _ = self.get_asset_oid_by_name("HighPrecBatteryCapacity")
        oid_basic, dt_basic, oid_spec = self.get_asset_oid_by_name("BasicBatteryStatus")

        if oid_adv:
            self._update_oid_value(
                oid_adv, dt_adv, snmp_data_types.Gauge32(charge_level / 10)
            )
        if oid_hp:
            self._update_oid_value(oid_hp, dt_hp, snmp_data_types.Gauge32(charge_level))

        if not oid_basic:
            return

        if charge_level <= 100:
            low_bat_value = oid_spec["batteryLow"]
            self._update_oid_value(
                oid_basic, dt_basic, snmp_data_types.Integer32(low_bat_value)
            )
        elif old_level <= 100 < charge_level:
            norm_bat_value = oid_spec["batteryNormal"]
            self._update_oid_value(
                oid_basic, dt_basic, snmp_data_types.Integer32(norm_bat_value)
            )

    def get_asset_oid_by_name(self, oid_name):
        """Get oid by oid name"""

        with self._graph_ref.get_session() as db_s:
            oid_details = GraphReference.get_asset_oid_by_name(
                db_s, int(self._asset_key), oid_name
            )

        return oid_details

    def process_voltage(self, voltage):
        """Update oids associated with UPS voltage
        Args:
            voltage: new voltage value
        Returns:
            tuple: true if transfer to battery is needed, transfer reason
        """

        oid_in_adv, dt_in_adv, _ = self.get_asset_oid_by_name("AdvInputLineVoltage")
        oid_out_adv, dt_out_adv, _ = self.get_asset_oid_by_name("AdvOutputVoltage")

        oid_voltage_value = snmp_data_types.Gauge32(int(voltage))

        if oid_in_adv:
            self._update_oid_value(oid_in_adv, dt_in_adv, oid_voltage_value)

        # retrieve thresholds:
        oid_high_th, _, _ = self.get_asset_oid_by_name("AdvConfigHighTransferVolt")
        oid_low_th, _, _ = self.get_asset_oid_by_name("AdvConfigLowTransferVolt")

        if not oid_high_th or not oid_low_th:
            if oid_out_adv:
                self._update_oid_value(oid_out_adv, dt_out_adv, oid_voltage_value)

            return False, None

        high_th = self._get_oid_value(oid_high_th)
        low_th = self._get_oid_value(oid_low_th)

        # new voltage value is within the threasholds
        if oid_out_adv and (low_th < voltage < high_th):
            self._update_oid_value(oid_out_adv, dt_out_adv, oid_voltage_value)
            return False, None

        return True, 0 if voltage <= low_th else 1

    def _publish_battery(self):
        """Publish battery update"""
        StateManager.get_store().publish(
            RedisChannels.battery_update_channel, json.dumps({"key": self.key})
        )


class PDUStateManager(state_api.IPDUStateManager, StateManager):
    """Handles state logic for PDU asset """

    def _update_current(self, load):
        """Update OID associated with the current amp value """
        with self._graph_ref.get_session() as session:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(
                session, int(self._asset_key), "AmpOnPhase"
            )
            if oid:
                load = load if load >= 0 else 0
                self._update_oid_value(
                    oid, data_type, snmp_data_types.Gauge32(load * 10)
                )

    def _update_wattage(self, wattage):
        """Update OID associated with the current wattage draw """
        with self._graph_ref.get_session() as session:
            oid, data_type, _ = GraphReference.get_asset_oid_by_name(
                session, int(self._asset_key), "WattageDraw"
            )

        wattage = wattage if wattage >= 0 else 0
        if oid:
            self._update_oid_value(oid, data_type, snmp_data_types.Integer32(wattage))

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

    def _get_oid_value_by_name(self, oid_name):
        """Get value under object id name"""
        with self._graph_ref.get_session() as session:
            oid, parent_key = GraphReference.get_component_oid_by_name(
                session, self.key, oid_name
            )
        if oid:
            oid = "{}.{}".format(oid, str(self.key)[-1])
            return int(self._get_oid_value(oid, key=parent_key))

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
        return self._get_oid_value_by_name("OutletConfigPowerOffTime")

    def get_config_on_delay(self):
        return self._get_oid_value_by_name("OutletConfigPowerOnTime")


class StaticDeviceStateManager(state_api.IStaticDeviceManager, StateManager):
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


class PSUStateManager(StateManager):
    """Power Supply"""

    def __init__(self, asset_info):
        StateManager.__init__(self, asset_info)
        self._psu_number = int(repr(asset_info["key"])[-1])
        # self._sensor = SensorRepository(int(repr(asset_info['key'])[:-1])).get

    def get_psu_sensor_names(self):
        """Find out BMC-specific psu keys (voltage, status etc.)
        Returns:
            dict: key value pairs of sensor type / sensor name for the psu
        """
        with self._graph_ref.get_session() as db_s:
            return GraphReference.get_psu_sensor_names(db_s, self.key, self._psu_number)
