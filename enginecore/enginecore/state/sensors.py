
import os
import threading
import logging
import time
import operator

from enginecore.state.state_managers import StateManager
from enginecore.model.graph_reference import GraphReference


class SensorFileLocks():
    
    def __init__(self):
        self._s_file_locks = {}

    def __str__(self):
        return str(self._s_file_locks)

    def add_sensor_file_lock(self, sensor_name):
        self._s_file_locks[sensor_name] = threading.Lock()

    def get_lock(self, sensor_name):
        return self._s_file_locks[sensor_name]


class Sensor():
    """Aggregates sensor information """


    def __init__(self, sensor_dir, s_details, s_locks):
        self._s_dir = sensor_dir
        
        self._s_specs = s_details['specs']
        self._s_type = self._s_specs['type']
        self._s_name = self._s_specs['name']
        self._s_group = self._s_specs['group']

        self._thermal_t = {}
        self._thermal_t_name_fmt = "({event})s:[{source}]->t:[{target}]"

        self._graph_ref = GraphReference()

        if 'index' in self._s_specs:
            self._s_addr = hex(int(s_details['address_space']['address'], 16) + self._s_specs['index']) 
        else:
            self._s_addr = self._s_specs['address']

        s_locks.add_sensor_file_lock(self._s_name)
        
        # save file locks
        self._s_file_locks = s_locks
        self._s_thermal_event = threading.Event()

  

    def __str__(self):
        with self._graph_ref.get_session() as session:
            thermal_rel = GraphReference.get_affected_sensors(session, self._s_name)

            s_str = []
            s_str.append("[{}/{}]: '{}' located at {};".format(
                self._s_group, 
                self._s_type, 
                self._s_name,
                self._s_addr
            ))
            
            # display sensor file location
            s_str.append(" - Sensor File: '{}'".format(self._get_sensor_file_path()))

            # print any thermal connections
            if thermal_rel['targets']:

                targets = thermal_rel['targets']
                s_str.append(" - Thermal Impact:")
                
                # format relationships
                rfmt = "{:55}".format("{action} by {degrees}°/{rate} sec on '{event}' event up until {pauseAt}°")
                tfmt = lambda rel: (" | ").format().join(map(lambda r: rfmt.format(**r), rel))

                # add targets & relationships to the output
                list(map(lambda t: s_str.append("   --> t:[{}] {}".format(t['name'], tfmt(t['rel']))), targets))

            return '\n'.join(s_str)


    def _init_thermal_impact(self): 

        with self._graph_ref.get_session() as session:
            thermal_rel_details = GraphReference.get_affected_sensors(session, self._s_name)

            # for each target & for each set of relationships with the target
            for target in thermal_rel_details['targets']:
                for rel in target['rel']:

                    target_name = target['name']
                    source_event = rel['event']

                    if target_name not in self._thermal_t:
                        self._thermal_t[target_name] = {}
                    
                    self._thermal_t[target_name][source_event] = threading.Thread(
                        target=self._update_target_sensor,
                        args=(target_name, source_event, ),
                        name=self._thermal_t_name_fmt.format(
                            source=self._s_name, target=target_name, event=source_event
                        )
                    )

                    self._thermal_t[target_name][source_event].daemon = True
                    self._thermal_t[target_name][source_event].start()

    
    def _update_target_sensor(self, target, event):


        with self._graph_ref.get_session() as session:
            while True:

                self._s_thermal_event.wait()   

                rel_details = GraphReference.get_target_sensor(session, self.name, target, event)
                # logging.info('')
                # shut down thread upon relationship removal
                if not rel_details:
                    del self._thermal_t[target][event]
                    return

                rel = rel_details['rel']

                source_sensor_status = operator.eq if rel['event'] == 'down' else operator.ne
                arith_op = operator.add if rel['action'] == 'increase' else operator.sub
                bound_op = operator.lt if rel['action'] == 'increase' else operator.gt

                with self._s_file_locks.get_lock(target), open(os.path.join(self._s_dir, target), 'r+') as sf_handler:

                    current_value = int(sf_handler.read())
                    new_value = arith_op(current_value, int(rel['degrees']))

                    if source_sensor_status(int(self.sensor_value), 0):

                        needs_update = bound_op(new_value, rel['pauseAt'])
                        if not needs_update and bound_op(current_value, rel['pauseAt']):
                            needs_update = True
                            new_value = int(rel['pauseAt'])
                        
                        if needs_update:
                            logging.info(
                                "> Current sensor value: %s will be updated to %s", current_value, int(new_value)
                            )

                            sf_handler.seek(0)
                            sf_handler.truncate()
                            sf_handler.write(str(new_value))

                time.sleep(int(rel['rate']))


    def _get_sensor_file_path(self):
        return os.path.join(self._s_dir, self._get_sensor_file())


    def _get_sensor_file(self):
        return self.name


    def add_new_thermal_impact(self, target, event):
        if target in self._thermal_t and event in self._thermal_t:
            raise ValueError('Thread already exists')
        
        with self._graph_ref.get_session() as session:
            rel_details = GraphReference.get_target_sensor(session, self.name, target, event)
            print('RELATIONSHIP DETAILS:')
            print(rel_details)

            if target not in self._thermal_t:
                self._thermal_t[target] = {}
            

            self._thermal_t[target][event] = threading.Thread(
                target=self._update_target_sensor,
                args=(target, rel_details['rel']['event'],),
                name=self._thermal_t_name_fmt.format(source=self._s_name, target=target, event=event)
            )

            self._thermal_t[target][event].daemon = True
            self._thermal_t[target][event].start()

    @property
    def name(self):
        """Unique sensor name""" 
        return self._s_name


    @property
    def group(self):
        """Sensor group type"""
        return self._s_group


    @property
    def sensor_value(self):
        with open(self._get_sensor_file_path()) as sf_handler: 
            # print(sf_handler.read())
            return sf_handler.read()


    @sensor_value.setter
    def sensor_value(self, new_value):
        with open(self._get_sensor_file_path(), "w+") as filein:
            filein.write(str(new_value))


    def start_thermal_impact(self):
        """Enable thread execution responsible for thermal updates"""
        logging.info("Sensor:[%s] - initializing thermal processes", self._s_name)
        self._init_thermal_impact()
        self.enable_thermal_impact()
        
    def enable_thermal_impact(self):
        logging.info("Sensor:[%s] - enabling thermal impact", self._s_name)
        self._s_thermal_event.set()

    def disable_thermal_impact(self):
        """Disable thread execution responsible for thermal updates"""
        logging.info("Sensor:[%s] - disabling thermal impact", self._s_name)
        self._s_thermal_event.clear()
        # logging.info(self._s_thermal_event.is_set())
        # logging.info(self._thermal_t)


    def set_to_off(self):
        with open(self._get_sensor_file_path(), "w+") as filein:
            off_value = self._s_specs['offValue'] if 'offValue' in self._s_specs else 0
            filein.write(str(off_value))

    def set_to_defaults(self):
        """Reset the sensor value to the specified default value"""

        with open(self._get_sensor_file_path(), "w+") as filein:
            if self.group == 'fan':
                default_value = int(self._s_specs['defaultValue']*0.1)
            else:
                default_value = self._s_specs['defaultValue']
            
            off_value = self._s_specs['offValue'] if 'offValue' in self._s_specs else 0
            filein.write(str(default_value if 'defaultValue' in self._s_specs else off_value))

   

class SensorRepository():
    def __init__(self, server_key, enable_thermal=False):
        self._server_key = server_key
        
        self._graph_ref = GraphReference()
        self._sensor_file_locks = SensorFileLocks()

        self._sensor_dir = os.path.join(
            StateManager.get_temp_workplace_dir(),
            str(server_key),
            'sensor_dir'
        )
        
        self._sensors = {}

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                sensor = Sensor(self._sensor_dir, sensor_info, self._sensor_file_locks)
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
        repo_str.append(" - files for sensor readings are located at '{}'".format(self._sensor_dir))

        for s_name in self._sensors:
            repo_str.append(str(self._sensors[s_name]))

        return '\n\n'.join(repo_str)


    def enable_thermal_impact(self):
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            sensor.enable_thermal_impact()     

    def disable_thermal_impact(self):
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            sensor.disable_thermal_impact()

    def shut_down_sensors(self):
        
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group != 'temperature':
                sensor.set_to_off()

        self.disable_thermal_impact()
        
    def power_up_sensors(self):
        
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group != 'temperature':
                sensor.set_to_defaults()
        self.enable_thermal_impact()

    def get_sensor_by_name(self, name):
        return self._sensors[name]


    def adjust_thermal_sensors(self, old_ambient, new_ambient):

        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group == 'temperature':
                with self._sensor_file_locks.get_lock(sensor.name):
                    
                    old_sensor_value = int(sensor.sensor_value)
                    new_sensor_value = old_sensor_value - old_ambient + new_ambient if old_sensor_value else new_ambient

                    logging.info(
                        "Sensor:[%s] - value will be updated from %s° to %s° due to ambient changes (%s° -> %s°)", 
                        sensor.name,
                        old_sensor_value,
                        new_sensor_value,
                        old_ambient, 
                        new_ambient
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
    