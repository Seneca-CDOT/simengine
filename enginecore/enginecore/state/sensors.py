
import os
import threading

from enginecore.state.state_managers import StateManager
from enginecore.model.graph_reference import GraphReference


class Sensor():
    
    def __init__(self, sensor_dir, s_details):
        self._s_dir = sensor_dir
        self._s_type = s_details['specs']['type']

        if 'index' in s_details['specs']:
            self._s_addr = hex(int(s_details['address_space']['address'], 16) + s_details['specs']['index']) 
        else:
            self._s_addr = s_details['specs']['address']

        self._s_file_lock = threading.Lock()


    def _update_sensor_value(self, data):
        while self._s_file_lock.locked(): 
            continue
        
        self._s_file_lock.acquire()

        with open(self._get_sensor_file(), 'w') as sf_handler:
            return sf_handler.write(str(int(data)) + '\n')

        self._s_file_lock.release()

    def _get_sensor_file(self):
        return os.path.join(self._s_dir, '{}{}'.format(self._s_type, self._s_addr))


class SensorRepository():
    def __init__(self, server_key):
        self._server_key = server_key
        self._graph_ref = GraphReference()
        self._sensor_dir = os.path.join(
            StateManager.get_temp_workplace_dir(),
            str(server_key),
            'sensor_dir'
        )
        self._sensors = []

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                self._sensors.append(Sensor(self._sensor_dir, sensor_info))


    @property
    def sensor_dir(self):
        """Get temp IPMI state dir"""
        return self._sensor_dir