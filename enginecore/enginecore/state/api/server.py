"""Server interfaces for managing servers' states """
import json
from enum import Enum
import math
import random
import libvirt

from enginecore.model.graph_reference import GraphReference
import enginecore.model.system_modeler as sys_modeler
from enginecore.tools.recorder import RECORDER as record


from enginecore.state.redis_channels import RedisChannels
from enginecore.state.api.state import IStateManager
from enginecore.tools.randomizer import Randomizer, ChainedArgs
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.sensor.sensor import SensorGroups


@Randomizer.register
class IServerStateManager(IStateManager):
    """Server managing a vm (libvirt domain)"""

    def __init__(self, asset_info):
        super(IServerStateManager, self).__init__(asset_info)
        self._vm_conn = libvirt.open("qemu:///system")
        self._vm = self._vm_conn.lookupByName(asset_info["domainName"])

    def vm_is_active(self):
        """Check if vm is powered up"""
        return self._vm.isActive()

    def _power_off_vm(self):
        """Power of vm controlled by the server asset
        (note that both shut down & power off actions are using
        destroy vm method since graceful shutdown sometimes results in a 
        vm stuck)
        """
        if self._vm.isActive():
            self._vm.destroy()

    @Randomizer.randomize_method()
    def shut_down(self):
        self._power_off_vm()
        self._update_load(0.0)

        return super().shut_down()

    @Randomizer.randomize_method()
    def power_off(self):
        self._power_off_vm()
        self._update_load(0.0)

        return super().power_off()

    @Randomizer.randomize_method()
    def power_up(self):

        powered = self.status

        if powered and not self._vm.isActive():
            self._vm.create()

        if powered or math.isclose(self.input_voltage, 0.0):
            return powered

        powered = super().power_up()
        if not self._vm.isActive() and powered:
            self._vm.create()
            self._update_load(self.power_consumption / self.input_voltage)
        return powered


@Randomizer.register
class IBMCServerStateManager(IServerStateManager):
    """Interface for a server that supports BMC chip & IPMI
    Example:
        unlike server (simpler variation of this type), bmc-server exposes
        both BMC sensors & storage/hard drive settable properties related
        to storcli64.
    """

    class StorageRandProps(Enum):
        """Settable randomizable options for server storage devices"""

        pd_media_error_count = 0
        pd_other_error_count = 1
        pd_predictive_error_count = 2
        ctrl_memory_correctable_errors = 3
        ctrl_memory_uncorrectable_errors = 4

    def _get_rand_fan_sensor_value(self, sensor_name: str) -> int:
        """Get random fan sensor value (if sensor thresholds are present)
        Args:
            sensor_name: name of a fan sensor
        Raises:
            ValueError: when the sensor name provided does not
                       belong to a sensor of type fan
        Returns:
            Random RPM value divided by 10 (unit accepted by IPMI_sim) 
            if at least one lower & one upper thresholds are present,
            returns the old sensor value otherwise
        """

        sensor = SensorRepository(self.key).get_sensor_by_name(sensor_name)
        if sensor.group != SensorGroups.fan:
            raise ValueError('Only sensors of type "fan" are accepted')

        thresholds = sensor.thresholds
        get_th_by_group = lambda g: filter(lambda x: x.startswith(g), thresholds)

        lowest_th = min(get_th_by_group("l"), key=lambda x: thresholds[x])
        highest_th = max(get_th_by_group("u"), key=lambda x: thresholds[x])

        # no random generation for this sensor if thresholds are missing
        if not thresholds or not lowest_th or not highest_th:
            return round(sensor.sensor_value * 0.1)

        return round(
            random.randrange(thresholds[lowest_th], thresholds[highest_th]) * 0.1
        )

    def _get_rand_pd_properties(self) -> list:
        """Get random settable physical drive attributes
        such as error counts occurred while
        reading/writing & pd state
        """

        rand_err = lambda prop: random.randrange(
            *self.get_storage_randomizer_prop(prop)
        )

        return [
            {"state": random.choice(["Onln", "Offln"])},
            {"media_error_count": rand_err(self.StorageRandProps.pd_media_error_count)},
            {"other_error_count": rand_err(self.StorageRandProps.pd_other_error_count)},
            {
                "predictive_error_count": rand_err(
                    self.StorageRandProps.pd_predictive_error_count
                )
            },
        ]

    def _get_rand_ctrl_props(self) -> list:
        """Get random settable controller attributes such 
        as alarm state & memory errors"""

        rand_err = lambda prop: random.randrange(
            *self.get_storage_randomizer_prop(prop)
        )

        return [
            {"alarm": random.choice(["on", "off", "missing"])},
            {
                "mem_c_errors": rand_err(
                    self.StorageRandProps.ctrl_memory_correctable_errors
                )
            },
            {
                "mem_uc_errors": rand_err(
                    self.StorageRandProps.ctrl_memory_uncorrectable_errors
                )
            },
        ]

    def get_cpu_stats(self) -> list:
        """Get VM cpu stats (user_time, cpu_time etc. (see libvirt api))
        Returns:
            cpu statistics for all CPUs
        """
        return self._vm.getCPUStats(True)

    def get_server_drives(self, controller_num):
        """Get all the drives that are in the server"""
        with self._graph_ref.get_session() as session:
            return GraphReference.get_all_drives(session, self.key, controller_num)

    def get_fan_sensors(self):
        """Retrieve sensors of type "fan" """
        return SensorRepository(self.key).get_sensors_by_group(SensorGroups.fan)

    def set_storage_randomizer_prop(self, proptype: StorageRandProps, slc: slice):
        """Update properties of randomized storage arguments"""

        with self._graph_ref.get_session() as session:
            return GraphReference.set_storage_randomizer_prop(
                session, self.key, proptype.name, slc
            )

    def get_storage_randomizer_prop(self, proptype: StorageRandProps) -> slice:
        """Get a randrange associated with a particular storage device"""
        with self._graph_ref.get_session() as session:
            return GraphReference.get_storage_randomizer_prop(
                session, self.key, proptype.name
            )

    @record
    @Randomizer.randomize_method(
        ChainedArgs(
            [
                lambda self: random.choice(self.get_fan_sensors()).name,
                lambda self, sensor_name: self._get_rand_fan_sensor_value(sensor_name),
            ]
        )()
    )
    def update_sensor(self, sensor_name: str, value):
        """Update runtime value of the sensor belonging to this server
        Args:
            sensor_name: human-readable sensor name to be updated
            value: new sensor value. Value type depends on a sensor type,
                   but note that some sensors; (fans for example)
                   will have values multiplied by 10 (e.g. 120=1200RPM)
        """

        try:
            sensor = SensorRepository(self.key).get_sensor_by_name(sensor_name)
            sensor.sensor_value = value
        except KeyError as error:
            print("Server or Sensor does not exist: %s", str(error))

    @record
    @Randomizer.randomize_method(
        arg_defaults=ChainedArgs(
            [
                lambda self: random.randrange(0, self.controller_count),
                lambda self, ctrl_num: random.choice(
                    list(
                        map(lambda x: x["DID"], self.get_server_drives(ctrl_num)["pd"])
                    )
                ),
                lambda self, _: random.choice(self._get_rand_pd_properties()),
            ]
        )()
    )
    def set_physical_drive_prop(self, controller: int, did: int, properties: dict):
        """Update properties of a physical drive belonging to a RAID array
        Args:
            controller: id of the controller physical drive is member of
            did: DID - unique drive id
            properties: props associated with physical drive
                    such as drive state ('state') or error counts
                    ('media_error_count', 'other_error_count', 'predictive_error_count')
        """
        with self._graph_ref.get_session() as session:
            return GraphReference.set_physical_drive_prop(
                session, self.key, controller, did, properties
            )

    @record
    @Randomizer.randomize_method(
        arg_defaults=ChainedArgs(
            [
                lambda self: random.randrange(0, self.controller_count),
                lambda self, _: random.choice(self._get_rand_ctrl_props()),
            ]
        )()
    )
    def set_controller_prop(self, controller: int, properties: dict):
        """Update properties associated with a RAID controller
        Args:
            controller: id/number assigned to a controller
            properties: controller props including "alarm", correctable & uncorrectable 
                        errors as "mem_c_errors", "mem_uc_errors"
        """
        with self._graph_ref.get_session() as session:
            return GraphReference.set_controller_prop(
                session, self.key, controller, properties
            )

    @record
    @Randomizer.randomize_method(
        arg_defaults=ChainedArgs(
            [
                lambda self: random.randrange(0, self.controller_count),
                lambda self, _: random.choice(["Yes", "No"]),
                lambda self, _: bool(random.getrandbits(1)),
            ]
        )()
    )
    def set_cv_replacement(self, controller: int, repl_status: str, wt_on_fail: bool):
        """Update Cachevault replacement status"""
        with self._graph_ref.get_session() as session:
            return GraphReference.set_cv_replacement(
                session, self.key, controller, repl_status, wt_on_fail
            )

    @property
    def cpu_load(self) -> int:
        """Get latest recorded CPU load in percentage (between 0 and 100)"""
        cpu_load = IStateManager.get_store().get(self.redis_key + ":cpu_load")
        return int(cpu_load.decode()) if cpu_load else 0

    @property
    def controller_count(self) -> int:
        """Find number of RAID controllers"""
        with self._graph_ref.get_session() as session:
            return GraphReference.get_controller_count(session, self.key)

    @classmethod
    def get_sensor_definitions(cls, asset_key):
        """Get sensor definitions """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            return GraphReference.get_asset_sensors(session, asset_key)

    @classmethod
    def update_thermal_sensor_target(cls, attr):
        """Create new or update existing thermal relationship between 2 sensors"""
        new_rel = sys_modeler.set_thermal_sensor_target(attr)
        if not new_rel:
            return

        IStateManager.get_store().publish(
            RedisChannels.sensor_conf_th_channel,
            json.dumps(
                {
                    "key": attr["asset_key"],
                    "relationship": {
                        "source": attr["source_sensor"],
                        "target": attr["target_sensor"],
                        "event": attr["event"],
                    },
                }
            ),
        )

    @classmethod
    def update_thermal_storage_target(cls, attr):
        """Add new storage entity affected by a sensor 
        Notify sensors if the relationship is new"""

        new_rel = sys_modeler.set_thermal_storage_target(attr)
        if not new_rel:
            return

        target_data = {
            "key": attr["asset_key"],
            "relationship": {
                "source": attr["source_sensor"],
                "event": attr["event"],
                "controller": attr["controller"],
            },
        }

        if "drive" in attr and attr["drive"]:
            channel = RedisChannels.str_drive_conf_th_channel
            target_data["relationship"]["drive"] = attr["drive"]
        else:
            channel = RedisChannels.str_cv_conf_th_channel
            target_data["relationship"]["cv"] = attr["cache_vault"]

        IStateManager.get_store().publish(channel, json.dumps(target_data))

    @classmethod
    def delete_thermal_storage_target(cls, attr):
        """Remove existing relationship between a sensor and a storage element"""
        return sys_modeler.delete_thermal_storage_target(attr)

    @classmethod
    def update_thermal_cpu_target(cls, attr):
        """Create new or update existing thermal
        relationship between CPU usage and sensor"""
        new_rel = sys_modeler.set_thermal_cpu_target(attr)
        if not new_rel:
            return

        IStateManager.get_store().publish(
            RedisChannels.cpu_usg_conf_th_channel,
            json.dumps(
                {
                    "key": attr["asset_key"],
                    "relationship": {"target": attr["target_sensor"]},
                }
            ),
        )

    @classmethod
    def get_thermal_cpu_details(cls, asset_key):
        """Query existing cpu->sensor relationship"""
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            return GraphReference.get_thermal_cpu_details(session, asset_key)


@Randomizer.register
class IPSUStateManager(IStateManager):
    """Exposes state logic for a server PSU asset """

    @Randomizer.randomize_method()
    def power_up(self):
        """Power up PSU"""

        powered = self.status

        if powered:
            return powered

        powered = super().power_up()
        if powered:
            if math.isclose(self.input_voltage, 0.0):
                psu_load = 0.0
            else:
                psu_load = self.power_consumption / self.input_voltage
            self._update_load(self.load + psu_load)
        return powered

    @property
    def supports_bmc(self):
        """Returns true if PSU is powering a server with BMC support"""
        return "ServerWithBMC" in self.asset_info["children"][0].labels
