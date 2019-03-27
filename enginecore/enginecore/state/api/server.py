import json

import libvirt


from enginecore.model.graph_reference import GraphReference
import enginecore.model.system_modeler as sys_modeler
from enginecore.state.recorder import RECORDER as record


from enginecore.state.redis_channels import RedisChannels
from enginecore.state.api.state import IStateManager


class IServerStateManager(IStateManager):
    def __init__(self, asset_info):
        super(IServerStateManager, self).__init__(asset_info)
        self._vm_conn = libvirt.open("qemu:///system")
        # TODO: error handling if the domain is missing (throws libvirtError) & close the connection
        self._vm = self._vm_conn.lookupByName(asset_info["domainName"])

    def vm_is_active(self):
        """Check if vm is powered up"""
        return self._vm.isActive()

    def shut_down(self):
        if self._vm.isActive():
            self._vm.destroy()
            self._update_load(0)
        return super().shut_down()

    def power_off(self):
        if self._vm.isActive():
            self._vm.destroy()
            self._update_load(0)
        return super().power_off()

    def power_up(self):
        powered = super().power_up()
        if not self._vm.isActive() and powered:
            self._vm.create()
            self._update_load(self.power_usage)
        return powered


class IBMCServerStateManager(IServerStateManager):
    """Interface for a server that supports BMC chip & IPMI
    Example:
        unlike server (simpler variation of this type), bmc-server exposes
        both BMC sensors & storage/hard drive settable properties related
        to storcli64.
    """

    def get_cpu_stats(self) -> list:
        """Get VM cpu stats (user_time, cpu_time etc. (see libvirt api))
        Returns:
            cpu statistics for all CPUs
        """
        return self._vm.getCPUStats(True)

    @record
    def update_sensor(self, sensor_name: str, value):
        """Update runtime value of the sensor belonging to this server
        Args:
            sensor_name: human-readable sensor name to be updated
            value: new sensor value. Value type depends on a sensor type, but note that some sensors
                   (fans for example) will have values multiplied by 10 (e.g. 120=1200RPM)
        """

        try:
            # import is inside the method to avoid circular imports
            from enginecore.state.sensor.repository import SensorRepository

            sensor = SensorRepository(self.key).get_sensor_by_name(sensor_name)
            sensor.sensor_value = value
        except KeyError as error:
            print("Server or Sensor does not exist: %s", str(error))

    @record
    def set_physical_drive_prop(self, controller: int, did: int, properties: dict):
        """Update properties of a physical drive belonging to a RAID array
        Args:
            controller: id of the controller physical drive is member of
            did: DID - unique drive id
            properties: props associated with physical drive such as drive state ('state') or 
                        error counts ('media_error_count', 'other_error_count', 'predictive_error_count')
        """
        with self._graph_ref.get_session() as session:
            return GraphReference.set_physical_drive_prop(
                session, self.key, controller, did, properties
            )

    @record
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
        """Create new or update existing thermal relationship between CPU usage and sensor"""
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
