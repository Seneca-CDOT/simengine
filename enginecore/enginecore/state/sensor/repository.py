"""Sensor repository provides a centralised access to the BMC/IPMI sensors
present in a particular asset/machine
"""
import os
import logging

from enginecore.state.state_initializer import get_temp_workplace_dir
from enginecore.model.graph_reference import GraphReference

from enginecore.state.sensor.file_locks import SensorFileLocks
from enginecore.state.sensor.sensor import Sensor, SensorGroups

logger = logging.getLogger(__name__)


class SensorRepository:
    """A sensor repository for a particular IPMI device"""

    def __init__(self, server_key, enable_thermal=False):
        self._server_key = server_key

        self._graph_ref = GraphReference()
        self._sensor_file_locks = SensorFileLocks()

        self._sensor_dir = os.path.join(
            get_temp_workplace_dir(), str(server_key), "sensor_dir"
        )

        self._sensors = {}

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                sensor = Sensor(
                    self._sensor_dir,
                    server_key,
                    sensor_info,
                    self._sensor_file_locks,
                    graph_ref=self._graph_ref,
                )
                self._sensors[sensor.name] = sensor

        if enable_thermal:
            self._load_thermal = True

            if not os.path.isdir(self._sensor_dir):
                os.mkdir(self._sensor_dir)

            for s_name in self._sensors:
                self._sensors[s_name].set_to_defaults()

    def __str__(self):

        repo_str = []
        repo_str.append("Sensor Repository for Server {}".format(self._server_key))
        repo_str.append(
            " - files for sensor readings are located at '{}'".format(self._sensor_dir)
        )

        return "\n\n".join(
            repo_str + list(map(lambda sn: str(self._sensors[sn]), self._sensors))
        )

    def enable_thermal_impact(self):
        """Set thermal event switch """
        list(map(lambda sn: self._sensors[sn].enable_thermal_impact(), self._sensors))

    def disable_thermal_impact(self):
        """Clear thermal event switch"""
        list(map(lambda sn: self._sensors[sn].disable_thermal_impact(), self._sensors))

    def shut_down_sensors(self):
        """Set all sensors to offline"""
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group != SensorGroups.temperature:
                sensor.set_to_off()

        self.disable_thermal_impact()

    def power_up_sensors(self):
        """Set all sensors to online"""
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group != SensorGroups.temperature:
                sensor.set_to_defaults()
        self.enable_thermal_impact()

    def get_sensor_by_name(self, name):
        """Get a specific sensor by name"""
        return self._sensors[name]

    def get_sensors_by_group(self, group):
        """Get sensors by group name (temperature, fan etc) """

        sensors_in_group = filter(
            lambda k: self._sensors[k].group == group, self._sensors
        )
        return list(map(lambda k: self._sensors[k], sensors_in_group))

    def adjust_thermal_sensors(self, old_ambient, new_ambient):
        """Indicate an ambient update"""

        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group == SensorGroups.temperature:
                with self._sensor_file_locks.get_lock(sensor.name):

                    old_sensor_value = int(sensor.sensor_value)
                    new_sensor_value = (
                        old_sensor_value - old_ambient + new_ambient
                        if old_sensor_value
                        else new_ambient
                    )

                    logger.debug(
                        "Sensor:[%s] updated from %s° to %s° due to ambient changes (%s°)->(%s°)",
                        sensor.name,
                        old_sensor_value,
                        new_sensor_value,
                        old_ambient,
                        new_ambient,
                    )

                    sensor.sensor_value = int(new_sensor_value)

        if self._load_thermal is True:
            self._load_thermal = False

            for s_name in self._sensors:
                self._sensors[s_name].start_thermal_impact()

    @property
    def sensor_dir(self):
        """Get temp IPMI state dir"""
        return self._sensor_dir

    @property
    def sensors(self):
        """Get all sensors in a sensor repo"""
        return self._sensors

    @property
    def server_key(self):
        """Get key of the server repo belongs to"""
        return self._server_key

    def stop(self):
        """Closes all the open connections"""
        self._graph_ref.close()
