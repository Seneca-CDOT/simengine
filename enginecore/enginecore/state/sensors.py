
import os
import threading
import logging
import time

from enginecore.state.state_managers import StateManager
from enginecore.model.graph_reference import GraphReference


class SensorFileLocks():
    
    def __init__(self):
        self._s_file_locks = {}

    def add_sensor_file_lock(self, sensor_name):
        self._s_file_locks[sensor_name] = threading.Lock()

    def get_lock(self, sensor_name):
        return self._s_file_locks[sensor_name]

    def __str__(self):
        return str(self._s_file_locks)
    

class Sensor():
    
    def __init__(self, sensor_dir, s_details, s_locks):
        self._s_dir = sensor_dir
        s_specs = s_details['specs']

        self._s_type = s_specs['type']
        self._s_name = s_specs['name']

        self._graph_ref = GraphReference()

        if 'index' in s_specs:
            self._s_addr = hex(int(s_details['address_space']['address'], 16) + s_specs['index']) 
        else:
            self._s_addr = s_specs['address']

        with open(self._get_sensor_file_path(), "w+") as filein:
            filein.write(str(int(s_specs['defaultValue']*0.1) if 'defaultValue' in s_specs else 0))


        s_locks.add_sensor_file_lock(self._s_name)
        
        # save file locks
        self._s_file_locks = s_locks
        self._s_thermal_event = threading.Event()

        self._init_thermal_impact()


    def _init_thermal_impact(self):

        with self._graph_ref.get_session() as session:
            thermal_rel_details = GraphReference.get_affected_sensors(session, self._s_name)

            # for each target & for each set of relationships with the target
            for target in thermal_rel_details['targets']:
                for rel in target['rel']:
                    thermal_thread = threading.Thread(
                        target=self._update_target_sensor,
                        args=(target, rel,),
                        name="s:[{}]->t:[{}]".format(self._s_name, target['name'])
                    )

                    thermal_thread.daemon = True
                    thermal_thread.start()

    
    def _update_target_sensor(self, target, rel):
        
        while True:
            self._s_thermal_event.wait()
            
            try:
                self._s_file_locks.get_lock(target['name']).acquire()
                Sensor.update_sensor_value(
                    os.path.join(self._s_dir, target['name']),
                    lambda current_value: str(current_value + int(rel['degrees']))+'\n'
                )
            finally:
                self._s_file_locks.get_lock(target['name']).release()

            time.sleep(int(rel['rate']))


    @classmethod
    def update_sensor_value(cls, path, operation):
        with open(path, 'r+') as sf_handler:
    
            current_value = int(sf_handler.read())
            new_value = operation(current_value)
            logging.info("> Current sensor value: %s will be updated to %s", current_value, int(new_value))

            sf_handler.seek(0)
            sf_handler.truncate()
            sf_handler.write(new_value)
            

    def _get_sensor_file_path(self):
        return os.path.join(self._s_dir, self._get_sensor_file())

    def _get_sensor_file(self):
        return self.name


    @property
    def name(self):
        """Unique sensor name""" 
        return self._s_name


    def enable_thermal_impact(self):
        """Enable thread execution responsible for thermal updates"""
        self._s_thermal_event.set()


    def disable_thermal_impact(self):
        """Disable thread execution responsible for thermal updates"""        
        self._s_thermal_event.clear()


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

        os.mkdir(self._sensor_dir)
        self._sensors = {}

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                sensor = Sensor(self._sensor_dir, sensor_info, self._sensor_file_locks)
                self._sensors[sensor.name] = sensor

        for s_name in self._sensors:
            self._sensors[s_name].enable_thermal_impact()

        # time.sleep(10)
        # for sensor in self._sensors:
        #     sensor.disable_thermal_impact()

    @property
    def sensor_dir(self):
        """Get temp IPMI state dir"""
        return self._sensor_dir
    