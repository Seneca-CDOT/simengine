"""Aggregates sensor management tools """

import os
import threading
import logging
import time
import json
import operator
from random import randint

import enginecore.state.state_managers as sm 
from enginecore.model.graph_reference import GraphReference


class SensorFileLocks():
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


class Sensor():
    """Aggregates sensor information """


    def __init__(self, sensor_dir, server_key, s_details, s_locks):
        self._s_dir = sensor_dir
        self._server_key = server_key
        
        self._s_specs = s_details['specs']
        self._s_type = self._s_specs['type']
        self._s_name = self._s_specs['name']
        self._s_group = self._s_specs['group']

        self._th_sensor_t = {}
        self._th_cpu_t = None

        self._th_sensor_t_name_fmt = "({event})s:[{source}]->t:[{target}]"
        self._th_cpu_t_name_fmt = "s:[cpu_load]->t:[{target}]"

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
            thermal_rel = GraphReference.get_affected_sensors(session, self._server_key, self._s_name)

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
                mfmt = "{:55}".format("{action} using {model} model every {rate} sec on, limit at {pauseAt}°")

                map_to_rel_format = lambda r: mfmt.format(**r) if 'model' in r else rfmt.format(**r)
                tfmt = lambda rel: (" | ").format().join(map(map_to_rel_format, rel))

                # add targets & relationships to the output
                list(map(lambda t: s_str.append("   --> t:[{}] {}".format(t['name'], tfmt(t['rel']))), targets))

            return '\n'.join(s_str)


    def _launch_thermal_sensor_thread(self, target, event):
        """Add a new impact thread 
        Args:
            target(str): name of the target sensor current sensor is affecting
            event(str): name of the source event affecting target sensor
        """
        
        if target not in self._th_sensor_t:
            self._th_sensor_t[target] = {}

        self._th_sensor_t[target][event] = threading.Thread(
            target=self._target_sensor_impact,
            args=(target, event, ),
            name=self._th_sensor_t_name_fmt.format(
                source=self._s_name, target=target, event=event
            )
        )

        self._th_sensor_t[target][event].daemon = True
        self._th_sensor_t[target][event].start()


    def _launch_thermal_cpu_thread(self):
        """Enable CPU impact upon the sensor
        """
        self._th_cpu_t = threading.Thread(
            target=self._cpu_impact,
            name=self._th_cpu_t_name_fmt.format(target=self.name)
        )

        self._th_cpu_t.daemon = True
        self._th_cpu_t.start()


    def _init_thermal_impact(self): 
        """Initialize thermal imact based on the saved inter-connections"""
    
        with self._graph_ref.get_session() as session:
            thermal_rel_details = GraphReference.get_affected_sensors(session, self._server_key, self._s_name)

            # for each target & for each set of relationships with the target
            for target in thermal_rel_details['targets']:
                for rel in target['rel']:
                    self._launch_thermal_sensor_thread(target['name'], rel['event'])

        self._launch_thermal_cpu_thread()


    def _calc_approx_value(self, model, current_value, inverse=False):
        """Approximate value based on the model provided"""

        nbr_model_key = min(model, key=lambda x: abs(int(x)-current_value))
        nbr_value = int(model[nbr_model_key])
        
        multiplier = int(nbr_model_key if inverse else current_value)
        divisor = int(current_value if inverse else nbr_model_key)

        return int((nbr_value * multiplier) / int(divisor))


    def _cpu_impact(self):
        """Keep updating this sensor based on cpu load changes
        This function waits for the thermal event switch and exits when the connection between this sensor & cpu load
        is removed;
        """

        with self._graph_ref.get_session() as session:

            asset_info = GraphReference.get_asset_and_components(session, self._server_key)
            server_sm = sm.BMCServerStateManager(asset_info)

            cpu_impact_degrees_1 = 0
            cpu_impact_degrees_2 = 0

            while True:
                self._s_thermal_event.wait()

                rel_details = GraphReference.get_cpu_thermal_rel(session, self._server_key, self.name)

                # relationship was deleted
                if not rel_details:
                    return
                
                with self._s_file_locks.get_lock(self.name):

                    current_cpu_load = server_sm.cpu_load

                    # calculate cpu impact based on the model
                    cpu_impact_degrees_2 = self._calc_approx_value(json.loads(rel_details['model']), current_cpu_load)
                    new_calc_value = int(self.sensor_value) + cpu_impact_degrees_2 - cpu_impact_degrees_1

                    # meaning update is needed
                    if cpu_impact_degrees_1 != cpu_impact_degrees_2:
                        ambient = sm.StateManager.get_ambient()
                        self.sensor_value = new_calc_value if new_calc_value > ambient else int(ambient)
  
                        logging.info(
                            'Thermal impact of CPU load at (%s%%) updated: (%s°)->(%s°)', 
                            current_cpu_load,
                            cpu_impact_degrees_1,
                            cpu_impact_degrees_2
                        )

                    cpu_impact_degrees_1 = cpu_impact_degrees_2
                    time.sleep(5)


    
    def _target_sensor_impact(self, target, event):
        """Keep updating the target sensor based on the relationship between this sensor and the target;
        This function waits for the thermal event switch and exits when the connection between source & target
        is removed;
        Args:
            target(str): name of the target sensor
            event(str): name of the event that enables thermal impact
        """

        with self._graph_ref.get_session() as session:
            while True:

                self._s_thermal_event.wait()   

                rel_details = GraphReference.get_sensor_thermal_rel(
                    session, self._server_key, relationship={'source': self.name, 'target': target, 'event': event}
                )

                # shut down thread upon relationship removal
                if not rel_details:
                    del self._th_sensor_t[target][event]
                    return

                rel = rel_details['rel']
                causes_heating = rel['action'] == 'increase'
                
                source_sensor_status = operator.eq if rel['event'] == 'down' else operator.ne
                bound_op = operator.lt  if causes_heating else operator.gt
                arith_op = operator.add if causes_heating else operator.sub

                # if model is specified -> use the runtime mappings
                if 'model' in rel and rel['model']:

                    calc_new_sv = arith_op
                    arith_op = lambda sv, _: calc_new_sv(sv, self._calc_approx_value(
                        json.loads(rel['model']), int(self.sensor_value)*10
                    ))

                    source_sensor_status = operator.ne


                # verify that sensor value doesn't go below room temp
                if causes_heating or rel['pauseAt'] > sm.StateManager.get_ambient():
                    pause_at = rel['pauseAt'] 
                else:
                    pause_at = sm.StateManager.get_ambient()

                # update target sensor value
                with self._s_file_locks.get_lock(target), open(os.path.join(self._s_dir, target), 'r+') as sf_handler:

                    current_value = int(sf_handler.read())
        
                    change_by = int(rel['degrees']) if 'degrees' in rel and rel['degrees'] else 0
                    new_sensor_value = arith_op(current_value, change_by)

                    # Source sensor status activated thermal impact
                    if source_sensor_status(int(self.sensor_value), 0):
                        needs_update = bound_op(new_sensor_value, pause_at)
                        if not needs_update and bound_op(current_value, pause_at):
                            needs_update = True
                            new_sensor_value = int(pause_at)
                        
                        if needs_update:
                            logging.info(
                                "Current sensor value (%s°) will be updated to %s°", 
                                current_value, 
                                int(new_sensor_value)
                            )
                            
                            sf_handler.seek(0)
                            sf_handler.truncate()
                            sf_handler.write(str(new_sensor_value))



                time.sleep(int(rel['rate']))


    def _get_sensor_file_path(self):
        """Full path to the sensor file"""
        return os.path.join(self._s_dir, self._get_sensor_filename())


    def _get_sensor_filename(self):
        """Name of the file sensor is pulling data from"""
        return self.name


    def add_sensor_thermal_impact(self, target, event):
        """Set a target sensor that will be affected by the current source sensor values
        Args:
            target(str): Name of the target sensor
            event(str): Source event causing the thermal impact to trigger
        """
        if target in self._th_sensor_t and event in self._th_sensor_t:
            raise ValueError('Thread already exists')
        
        with self._graph_ref.get_session() as session:
            
            rel_details = GraphReference.get_sensor_thermal_rel(
                session, self._server_key, relationship={'source': self.name, 'target': target, 'event': event}
            )

            if rel_details:
                self._launch_thermal_sensor_thread(target, rel_details['rel']['event'])


    def add_cpu_thermal_impact(self):
        """Set this sensor as one affected by the CPU-load
        """
        self._launch_thermal_cpu_thread()


    @property
    def name(self):
        """Unique sensor name""" 
        return self._s_name


    @property
    def group(self):
        """Sensor group type (datatype, e.g. temperature, voltage)"""
        return self._s_group


    @property
    def sensor_value(self):
        """Current sensor reading value"""
        with open(self._get_sensor_file_path()) as sf_handler: 
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
        # logging.info(self._th_sensor_t)


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
    """A sensor repository for a particular IPMI device"""

    def __init__(self, server_key, enable_thermal=False):
        self._server_key = server_key
        
        self._graph_ref = GraphReference()
        self._sensor_file_locks = SensorFileLocks()

        self._sensor_dir = os.path.join(
            sm.StateManager.get_temp_workplace_dir(),
            str(server_key),
            'sensor_dir'
        )
        
        self._sensors = {}

        with self._graph_ref.get_session() as session:
            sensors = GraphReference.get_asset_sensors(session, server_key)
            for sensor_info in sensors:
                sensor = Sensor(self._sensor_dir, server_key, sensor_info, self._sensor_file_locks)
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

        return '\n\n'.join(repo_str + list(map(lambda sn: str(self._sensors[sn]), self._sensors)))


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
            if sensor.group != 'temperature':
                sensor.set_to_off()

        self.disable_thermal_impact()
        

    def power_up_sensors(self):
        """Set all sensors to online"""
        for s_name in self._sensors:
            sensor = self._sensors[s_name]
            if sensor.group != 'temperature':
                sensor.set_to_defaults()
        self.enable_thermal_impact()


    def get_sensor_by_name(self, name):
        """Get a specific sensor by name"""
        return self._sensors[name]


    def adjust_thermal_sensors(self, old_ambient, new_ambient):
        """Indicate an ambient update"""
        
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
    