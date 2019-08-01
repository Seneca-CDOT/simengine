"""Sensor provides access to ipmi/bmc sensors & manages thermal relationships between
sensors & sensors, sensors & storage components, cpu & sensors
"""

import os
import threading
import logging
import time
import json
import operator
from collections import OrderedDict
from enum import Enum

from enginecore.state.api.environment import ISystemEnvironment
from enginecore.model.graph_reference import GraphReference

logger = logging.getLogger(__name__)


class HDComponents(Enum):
    """Thermal storage target types"""

    CacheVault = 1
    PhysicalDrive = 2


class SensorGroups(Enum):
    """Valid sensor groups"""

    psu = 1
    current = 2
    fan = 3
    voltage = 4
    wattage = 5
    temperature = 6


class Sensor:

    """Aggregates sensor information """

    thresholds_types = ["lnr", "lcr", "lnc", "unc", "ucr", "unr"]

    def __init__(self, sensor_dir, server_key, s_details, s_locks, graph_ref):
        self._s_dir = sensor_dir
        self._server_key = server_key

        self._s_specs = s_details["specs"]
        self._s_address_space = s_details["address_space"]

        self._s_type = self._s_specs["type"]
        self._s_name = self._s_specs["name"]

        self._s_group = SensorGroups[self._s_specs["group"]]

        self._th_sensor_t = {}
        self._th_storage_t = {}
        self._th_cpu_t = None

        self._th_sensor_t_name_fmt = "({event})s:[{source}]->t:[{target}]"
        self._th_storage_t_name_fmt = (
            "({event})s:[{source}]->STORAGE:t:[c{ctrl}/{target}]"
        )

        self._th_cpu_t_name_fmt = "s:[cpu_load]->t:[{target}]"

        self._graph_ref = graph_ref

        if "index" in self._s_specs:
            self._s_addr = hex(
                int(s_details["address_space"]["address"], 16) + self._s_specs["index"]
            )
        else:
            self._s_addr = self._s_specs["address"]

        s_locks.add_sensor_file_lock(self._s_name)

        # save file locks
        self._s_file_locks = s_locks
        self._s_thermal_event = threading.Event()

    def __str__(self):
        with self._graph_ref.get_session() as session:
            thermal_rel = GraphReference.get_affected_sensors(
                session, self._server_key, self._s_name
            )

            s_str = []
            s_str.append(
                "[{}/{}]: '{}' located at {};".format(
                    self._s_group, self._s_type, self._s_name, self._s_addr
                )
            )

            # display sensor file location
            s_str.append(" - Sensor File: '{}'".format(self._get_sensor_file_path()))

            # print any thermal connections
            if thermal_rel["targets"]:

                targets = thermal_rel["targets"]
                s_str.append(" - Thermal Impact:")

                # format relationships
                rfmt = "{:55}".format(
                    "{action} by {degrees}°/{rate} sec on '{event}' event up until {pauseAt}°"
                )
                mfmt = "{:55}".format(
                    "{action} using {model} model every {rate} sec on, limit at {pauseAt}°"
                )

                map_to_rel_format = (
                    lambda r: mfmt.format(**r) if "model" in r else rfmt.format(**r)
                )
                tfmt = lambda rel: (" | ").format().join(map(map_to_rel_format, rel))

                # add targets & relationships to the output
                list(
                    map(
                        lambda t: s_str.append(
                            "   --> t:[{}] {}".format(t["name"], tfmt(t["rel"]))
                        ),
                        targets,
                    )
                )

            return "\n".join(s_str)

    def _launch_thermal_sensor_thread(self, target, event):
        """Add a new impact thread 
        Args:
            target(str): name of the target sensor current sensor is affecting
            event(str): name of the source event affecting target sensor
        """

        if target not in self._th_sensor_t:
            self._th_sensor_t[target] = {}

        self._th_sensor_t[target][event] = threading.Thread(
            target=self._target_sensor,
            args=(target, event),
            name=self._th_sensor_t_name_fmt.format(
                source=self._s_name, target=target, event=event
            ),
        )

        self._th_sensor_t[target][event].daemon = True
        self._th_sensor_t[target][event].start()

    def _launch_thermal_cpu_thread(self):
        """Enable CPU impact upon the sensor
        """
        self._th_cpu_t = threading.Thread(
            target=self._cpu_impact,
            name=self._th_cpu_t_name_fmt.format(target=self.name),
        )

        self._th_cpu_t.daemon = True
        self._th_cpu_t.start()

    def _launch_thermal_storage_thread(self, controller, hd_element, hd_type, event):

        thread_name = "{}-{}".format(hd_type.name, hd_element)
        if (
            thread_name in self._th_storage_t
            and event in self._th_storage_t[thread_name]
        ):
            raise ValueError("Thread already exists")
        if hd_element not in self._th_storage_t:
            self._th_storage_t[hd_element] = {}

        self._th_storage_t[hd_element][event] = threading.Thread(
            target=self._target_storage,
            args=(controller, hd_element, hd_type, event),
            name=self._th_storage_t_name_fmt.format(
                ctrl=controller, source=self._s_name, target=hd_element, event=event
            ),
        )

        self._th_storage_t[hd_element][event].daemon = True
        self._th_storage_t[hd_element][event].start()

    def _init_thermal_impact(self):
        """Initialize thermal imact based on the saved inter-connections"""

        with self._graph_ref.get_session() as session:
            thermal_sensor_rel_details = GraphReference.get_affected_sensors(
                session, self._server_key, self._s_name
            )

            # for each target & for each set of relationships with the target
            for target in thermal_sensor_rel_details["targets"]:
                for rel in target["rel"]:
                    self._launch_thermal_sensor_thread(target["name"], rel["event"])

            thermal_storage_rel_details = GraphReference.get_affected_hd_elements(
                session, self._server_key, self._s_name
            )

            for target in thermal_storage_rel_details["targets"]:
                if "DID" in target and target["DID"]:
                    hd_type = HDComponents.PhysicalDrive
                    hd_element = target["DID"]
                else:
                    hd_type = HDComponents.CacheVault
                    hd_element = target["serialNumber"]

                for rel in target["rel"]:
                    self._launch_thermal_storage_thread(
                        target["controller"]["controllerNum"],
                        hd_element,
                        hd_type,
                        rel["event"],
                    )

        self._launch_thermal_cpu_thread()

    def _calc_approx_value(self, model, current_value, inverse=False):
        """Approximate value based on the model provided"""

        nbr_model_key = min(model, key=lambda x: abs(int(x) - current_value))
        nbr_value = int(model[nbr_model_key])

        multiplier = int(nbr_model_key if inverse else current_value)
        divisor = int(current_value if inverse else nbr_model_key)

        return int((nbr_value * multiplier) / int(divisor))

    def _cpu_impact(self):
        """Keep updating *this sensor based on cpu load changes
        This function waits for the thermal event switch and exits when the connection between this sensor & cpu load
        is removed;
        """

        # avoid circular imports with the server
        from enginecore.state.api import IBMCServerStateManager

        with self._graph_ref.get_session() as session:

            asset_info = GraphReference.get_asset_and_components(
                session, self._server_key
            )
            server_sm = IBMCServerStateManager(asset_info)

            cpu_impact_degrees_1 = 0
            cpu_impact_degrees_2 = 0

            while True:
                self._s_thermal_event.wait()

                rel_details = GraphReference.get_cpu_thermal_rel(
                    session, self._server_key, self.name
                )

                # relationship was deleted
                if not rel_details:
                    return

                with self._s_file_locks.get_lock(self.name):

                    current_cpu_load = server_sm.cpu_load

                    # calculate cpu impact based on the model
                    cpu_impact_degrees_2 = self._calc_approx_value(
                        json.loads(rel_details["model"]), current_cpu_load
                    )
                    new_calc_value = (
                        int(self.sensor_value)
                        + cpu_impact_degrees_2
                        - cpu_impact_degrees_1
                    )

                    # meaning update is needed
                    if cpu_impact_degrees_1 != cpu_impact_degrees_2:
                        ambient = ISystemEnvironment.get_ambient()
                        self.sensor_value = (
                            new_calc_value if new_calc_value > ambient else int(ambient)
                        )

                        logger.debug(
                            "Thermal impact of CPU load at (%s%%) updated: (%s°)->(%s°)",
                            current_cpu_load,
                            cpu_impact_degrees_1,
                            cpu_impact_degrees_2,
                        )

                    cpu_impact_degrees_1 = cpu_impact_degrees_2
                    time.sleep(5)

    def _target_storage(self, controller, target, hd_type, event):
        with self._graph_ref.get_session() as session:
            while True:

                self._s_thermal_event.wait()

                # target
                if hd_type == HDComponents.CacheVault:
                    target_attr = "serialNumber"
                    target_value = '"{}"'.format(target)
                elif hd_type == HDComponents.PhysicalDrive:
                    target_attr = "DID"
                    target_value = target
                else:
                    raise ValueError("Unknown hardware component!")

                rel_details = GraphReference.get_sensor_thermal_rel(
                    session,
                    self._server_key,
                    relationship={
                        "source": self._s_name,
                        "target": {"attribute": target_attr, "value": target_value},
                        "event": event,
                    },
                )

                if not rel_details:
                    del self._th_storage_t[target][event]
                    return

                rel = rel_details["rel"]
                causes_heating = rel["action"] == "increase"
                source_sensor_status = (
                    operator.eq if rel["event"] == "down" else operator.ne
                )

                # if model is specified -> use the runtime mappings
                if "model" in rel and rel["model"]:
                    rel["degrees"] = self._calc_approx_value(
                        json.loads(rel["model"]), int(self.sensor_value) * 10
                    )

                    source_sensor_status = operator.ne

                if source_sensor_status(int(self.sensor_value), 0):
                    updated, new_temp = GraphReference.add_to_hd_component_temperature(
                        session,
                        target={
                            "server_key": self._server_key,
                            "controller": controller,
                            "attribute": target_attr,
                            "value": target_value,
                            "hd_type": hd_type.name,
                        },
                        temp_change=rel["degrees"] * 1 if causes_heating else -1,
                        limit={
                            "lower": ISystemEnvironment.get_ambient(),
                            "upper": rel["pauseAt"] if causes_heating else None,
                        },
                    )

                    if updated:
                        logger.info("temperature sensor was updated to %s°", new_temp)

                time.sleep(rel["rate"])

    def _target_sensor(self, target, event):
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
                    session,
                    self._server_key,
                    relationship={
                        "source": self.name,
                        "target": {"attribute": "name", "value": '"{}"'.format(target)},
                        "event": event,
                    },
                )

                # shut down thread upon relationship removal
                if not rel_details:
                    del self._th_sensor_t[target][event]
                    return

                rel = rel_details["rel"]
                causes_heating = rel["action"] == "increase"

                source_sensor_status = (
                    operator.eq if rel["event"] == "down" else operator.ne
                )
                bound_op = operator.lt if causes_heating else operator.gt
                arith_op = operator.add if causes_heating else operator.sub

                # if model is specified -> use the runtime mappings
                if "model" in rel and rel["model"]:

                    calc_new_sv = arith_op
                    arith_op = lambda sv, _: calc_new_sv(
                        sv,
                        self._calc_approx_value(
                            json.loads(rel["model"]), int(self.sensor_value) * 10
                        ),
                    )

                    source_sensor_status = operator.ne

                # verify that sensor value doesn't go below room temp
                if causes_heating or rel["pauseAt"] > ISystemEnvironment.get_ambient():
                    pause_at = rel["pauseAt"]
                else:
                    pause_at = ISystemEnvironment.get_ambient()

                # update target sensor value
                with self._s_file_locks.get_lock(target), open(
                    os.path.join(self._s_dir, target), "r+"
                ) as sf_handler:

                    current_value = int(sf_handler.read())

                    change_by = (
                        int(rel["degrees"])
                        if "degrees" in rel and rel["degrees"]
                        else 0
                    )
                    new_sensor_value = arith_op(current_value, change_by)

                    # Source sensor status activated thermal impact
                    if source_sensor_status(int(self.sensor_value), 0):
                        needs_update = bound_op(new_sensor_value, pause_at)
                        if not needs_update and bound_op(current_value, pause_at):
                            needs_update = True
                            new_sensor_value = int(pause_at)

                        if needs_update:
                            logger.info(
                                "Current sensor value (%s°) will be updated to %s°",
                                current_value,
                                int(new_sensor_value),
                            )

                            sf_handler.seek(0)
                            sf_handler.truncate()
                            sf_handler.write(str(new_sensor_value))

                time.sleep(int(rel["rate"]))

    def _get_sensor_file_path(self):
        """Full path to the sensor file"""
        return os.path.join(self._s_dir, self._get_sensor_filename())

    def _get_sensor_filename(self):
        """Name of the file sensor is pulling data from"""
        return self.name

    def add_cv_thermal_impact(self, controller, cv, event):
        self._launch_thermal_storage_thread(
            controller, cv, HDComponents.CacheVault, event
        )

    def add_pd_thermal_impact(self, controller, pd, event):
        self._launch_thermal_storage_thread(
            controller, pd, HDComponents.PhysicalDrive, event
        )

    def add_sensor_thermal_impact(self, target, event):
        """Set a target sensor that will be affected by the current source sensor values
        Args:
            target(str): Name of the target sensor
            event(str): Source event causing the thermal impact to trigger
        """
        if target in self._th_sensor_t and event in self._th_sensor_t[target]:
            raise ValueError("Thread already exists")

        with self._graph_ref.get_session() as session:

            rel_details = GraphReference.get_sensor_thermal_rel(
                session,
                self._server_key,
                relationship={
                    "source": self.name,
                    "target": {"attribute": "name", "value": '"{}"'.format(target)},
                    "event": event,
                },
            )

            if rel_details:
                self._launch_thermal_sensor_thread(target, rel_details["rel"]["event"])

    def add_cpu_thermal_impact(self):
        """Set this sensor as one affected by the CPU-load
        """
        self._launch_thermal_cpu_thread()

    @property
    def name(self):
        """Unique sensor name"""
        return self._s_name

    @property
    def sensor_type(self):
        """Sensor type (one of enginecore.model.supported_sensors)"""
        return self._s_type

    @property
    def group(self):
        """Sensor group type (datatype, e.g. temperature, voltage)"""
        return self._s_group

    @property
    def sensor_value(self):
        """Current sensor reading value"""
        with open(self._get_sensor_file_path()) as sf_handler:
            return sf_handler.read()

    @property
    def thresholds(self):
        """Get sensor thresholds (if supported by the sensor)
        Returns:
            OrderedDict: annotated sensor threshold values ordered from lower to upper as
                         ("lnr", "lcr", "lnc", "unc", "ucr", "unr")
        """
        return OrderedDict(
            [
                (k, self._s_specs[k])
                for k in Sensor.thresholds_types
                if k in self._s_specs
            ]
        )

    @property
    def event(self):
        """Event associated with a type"""
        return 8 if self.event_reading_type != 1 else 3

    @property
    def event_reading_type(self):
        """Get event reading type"""
        return (
            self._s_specs["eventReadingType"]
            if "eventReadingType" in self._s_specs
            else 1
        )

    @property
    def index(self):
        """Get sensor index if sensor is part of an address space"""
        return self._s_specs["index"] if "index" in self._s_specs else None

    @property
    def address(self):
        """Get sensor address"""
        if self.index is not None:
            return hex(int(self._s_address_space["address"], 16) + self.index)
        return self._s_specs["address"]

    @sensor_value.setter
    def sensor_value(self, new_value):
        with open(self._get_sensor_file_path(), "w+") as filein:
            filein.write(str(new_value))

    def start_thermal_impact(self):
        """Enable thread execution responsible for thermal updates"""
        self._init_thermal_impact()
        self.enable_thermal_impact()

    def enable_thermal_impact(self):
        self._s_thermal_event.set()

    def disable_thermal_impact(self):
        """Disable thread execution responsible for thermal updates"""
        self._s_thermal_event.clear()

    def set_to_off(self):
        with open(self._get_sensor_file_path(), "w+") as filein:
            off_value = self._s_specs["offValue"] if "offValue" in self._s_specs else 0
            filein.write(str(off_value))

    def set_to_defaults(self):
        """Reset the sensor value to the specified default value"""

        with open(self._get_sensor_file_path(), "w+") as filein:
            if self.group == SensorGroups.fan:
                default_value = int(self._s_specs["defaultValue"] * 0.1)
            else:
                default_value = self._s_specs["defaultValue"]

            off_value = self._s_specs["offValue"] if "offValue" in self._s_specs else 0
            filein.write(
                str(default_value if "defaultValue" in self._s_specs else off_value)
            )
