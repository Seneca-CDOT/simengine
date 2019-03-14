"""Threa-safe locks for sensors & sensor repository"""
import threading


class SensorFileLocks:
    """File locks for sensor files for safe access"""

    def __init__(self):
        self._s_file_locks = {}

    def __str__(self):
        return str(self._s_file_locks)

    def add_sensor_file_lock(self, sensor_name):
        """Add new lock"""
        self._s_file_locks[sensor_name] = threading.Lock()

    def get_lock(self, sensor_name):
        """Get file lock by sensor name"""
        return self._s_file_locks[sensor_name]
