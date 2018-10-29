
import os
import threading

from enginecore.state.state_managers import StateManager
from enginecore.model.graph_reference import GraphReference


class SensorFileLocks():
    
    def __init__(self):
        self._s_file_locks = {}

    def add_sensor_file_lock(self, filename):
        self._s_file_locks[filename] = threading.Lock()

    def get_lock(self, filename):
        return self._s_file_locks[filename]

    def __str__(self):
        return str(self._s_file_locks)
    
class Sensor():
    
    def __init__(self, sensor_dir, s_details, s_locks):
        self._s_dir = sensor_dir
        self._s_type = s_details['specs']['type']
        self._graph_ref = GraphReference()

        if 'index' in s_details['specs']:
            self._s_addr = hex(int(s_details['address_space']['address'], 16) + s_details['specs']['index']) 
        else:
            self._s_addr = s_details['specs']['address']

        s_locks.add_sensor_file_lock(self._get_sensor_file())
        self._s_file_locks = s_locks
        self._s_thermal_event = threading.Event()


    def _thermal_impact(self):
        while True:
            # block execution
            self._s_thermal_event.wait()

            # # 
            # with self._graph_ref.get_session() as session:
            #      sensors = GraphReference.get_affected_sensors(session, server_key)


    def _update_sensor_value(self, data):
        # try:

        # finally:
        #   release the lock
        # while self._s_file_locks[].locked(): 
        #     continue
        
        # self._s_file_lock.acquire()

        with open(self._get_sensor_file_path(), 'w') as sf_handler:
            return sf_handler.write(str(int(data)) + '\n')

        # self._s_file_locks.release()

    def _get_sensor_file_path(self):
        return os.path.join(self._s_dir, self._get_sensor_file())
        
    def _get_sensor_file(self):
        return '{}{}'.format(self._s_type, self._s_addr)



class SensorRepository():
    def __init__(self, server_key):
        self._server_key = server_key
        
        self._graph_ref = GraphReference()
        self._sensor_file_locks = SensorFileLocks()

        self._sensor_dir = os.path.join(
            StateManager.get_temp_workplace_dir(),
            str(server_key),
            'sensor_dir'
        )
        self._sensors = []

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                self._sensors.append(Sensor(self._sensor_dir, sensor_info, self._sensor_file_locks))


    @property
    def sensor_dir(self):
        """Get temp IPMI state dir"""
        return self._sensor_dir
    