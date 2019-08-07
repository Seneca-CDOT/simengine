"""IPMI LAN BMC Simulator that can be accessed using the IPMI 1.5 or 2.0 protocols
This wrapper can configure sensor definitions & manage ipmi_sim program instance 
"""

import os
import subprocess
import logging
from distutils import dir_util
import sysconfig

from string import Template

from enginecore.model.supported_sensors import SUPPORTED_SENSORS
from enginecore.state.agent.agent import Agent

logger = logging.getLogger(__name__)


class IPMIAgent(Agent):
    """Python wrapper managing ipmi_sim program that takes 
    SensorRepository & translates it into ipmi_sim sensor definitions.
    """

    supported_sensors = dict.fromkeys(SUPPORTED_SENSORS, "")
    lan_conf_attributes = [
        "host",
        "port",
        "user",
        "password",
        "interface",
        "vmport",
        "num_components",
    ]

    def __init__(self, ipmi_dir, ipmi_config, sensor_repo, bmc_address="0x20"):
        """Initialize ipmi_sim working environment, define sensors
        based on sensor repository and start ipmi_sim program.
        Args:
            ipmi_dir(str): path to simulator's work environment
            ipmi_config(dict): connection & network device configuration
                               (see IPMIAgent.lan_conf_attributes)
            sensor_repo(SensorRepository): BMC sensors belonging to a particular server
            bmc_address(str): baseboard address to be used
        """
        super(IPMIAgent, self).__init__()

        self._ipmi_dir = ipmi_dir
        self._ipmi_config = ipmi_config
        self._sensor_repo = sensor_repo
        self._bmc_address = bmc_address

        # initialize ipmi_sim environment
        self._init_ipmi_dir()
        self._init_sensor_defs()
        self._compile_sensors()
        self._update_permissions()

        # start process
        self.start_agent()

    def _substitute_template_file(self, filename, options):
        """Update file using templating
        Args:
            filename(str): path to a template file to be populated
            options(dict): contains template key/values
        """
        with open(filename, "r+", encoding="utf-8") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(options))

    def _init_sensor_defs(self):
        """Populate template files with sensors"""

        # Template options
        lan_conf_opt = {
            "asset_key": self._sensor_repo.server_key,
            "extend_lib": self.extend_plugin_path,
            "lan_path": os.path.join(
                os.environ["SIMENGINE_IPMI_TEMPL"], "ipmi_sim_lancontrol"
            ),
            **self._ipmi_config,
        }

        ipmisim_emu_opt = {"ipmi_dir": self._ipmi_dir, **IPMIAgent.supported_sensors}

        sdrs_opt = {
            "ipmi_dir": self._ipmi_dir,
            "includes": "",
            **IPMIAgent.supported_sensors,
        }

        # initialize sensors
        for i, sensor_name in enumerate(self._sensor_repo.sensors):

            sensor = self._sensor_repo.sensors[sensor_name]
            s_type = sensor.sensor_type

            index = str(sensor.index + 1) if sensor.index else ""

            # define a few variables (sensor index, id and address)
            sdrs_opt[s_type] += 'define IDX "{}" \n'.format(index)
            sdrs_opt[s_type] += 'define ID_STR "{}" \n'.format(i)
            sdrs_opt[s_type] += 'define ADDR "{}" \n'.format(sensor.address)

            sensor_th = sensor.thresholds

            # add thresholds definition
            for th_type in sensor.thresholds_types:
                th_value = sensor_th[th_type] if th_type in sensor_th else 0
                sdrs_opt[s_type] += 'define {} "{}"\n'.format(th_type.upper(), th_value)

                sdrs_opt[s_type] += 'define R_{} "{}"\n'.format(
                    th_type.upper(), th_type in sensor_th
                )

            sdrs_opt[s_type] += 'define C_NAME "{}" \n'.format(sensor.name)
            sdrs_opt[s_type] += 'include "{}/{}.sdrs" \n'.format(self._ipmi_dir, s_type)

            # add sensor .emu command in format:
            # sensor_add <address & type> <poll file location>
            ipmisim_emu_opt[s_type] += "sensor_add {} 0 {} {} {} ".format(
                self._bmc_address,
                sensor.address,
                sensor.event,
                sensor.event_reading_type,
            )
            ipmisim_emu_opt[
                s_type
            ] += 'poll 2000 file $TEMP_IPMI_DIR"/sensor_dir/{}" \n'.format(sensor.name)

        # Set server-specific includes
        if self._ipmi_config["num_components"] == 2:
            ipmisim_emu_opt["includes"] = 'include "{}"'.format(
                os.path.join(self._ipmi_dir, "ipmisim1_psu.emu")
            )
            sdrs_opt["includes"] = 'include "{}"'.format(
                os.path.join(self._ipmi_dir, "main_dual_psu.sdrs")
            )

        # populate templates with options
        self._substitute_template_file(self.lan_conf_path, lan_conf_opt)
        self._substitute_template_file(self.ipmisim_emu_path, ipmisim_emu_opt)
        self._substitute_template_file(self.sensor_def_path, sdrs_opt)

    def _init_ipmi_dir(self):
        """Copy clean template files to the working ipmi directory"""

        # a workaround: https://stackoverflow.com/a/28055993
        # pylint: disable=W0212
        dir_util._path_created = {}
        # pylint: enable=W0212

        dir_util.copy_tree(os.environ.get("SIMENGINE_IPMI_TEMPL"), self._ipmi_dir)

    def _compile_sensors(self):
        """Compile SDRs sensor definitions"""
        os.system("sdrcomp -o {} {}".format(self.sdr_main_path, self.sensor_def_path))

    def _update_permissions(self):
        """Update recursively"""
        subprocess.call(["chmod", "-R", "ugo+rwx", self._ipmi_dir])

    @property
    def lan_conf_path(self):
        """Path to a config file containing communication parameters for the device"""
        return os.path.join(self._ipmi_dir, "lan.conf")

    @property
    def ipmisim_emu_path(self):
        """Path to a file containing .emu commands for creating IPMI system"""
        return os.path.join(self._ipmi_dir, "ipmisim1.emu")

    @property
    def sdr_main_path(self):
        """Path to the compiled IPMIsim sensors (compiled SDRs) """
        return os.path.join(
            self.emu_state_dir_path, "ipmi_sim", "ipmisim1", "sdr.20.main"
        )

    @property
    def emu_state_dir_path(self):
        """Path to the folder containing sensor compilations"""
        return os.path.join(self._ipmi_dir, "emu_state")

    @property
    def sensor_def_path(self):
        """Path to .sdrs file containing sensor definitions"""
        return os.path.join(self._ipmi_dir, "main.sdrs")

    @property
    def extend_plugin_path(self):
        """Path to the compiled .c simengine extension of IPMIsim"""
        return os.path.join(
            sysconfig.get_config_var("LIBDIR"), "simengine", "haos_extend.so"
        )

    def start_agent(self):
        """Start up new ipmi_sim process"""

        cmd = (
            ["ipmi_sim"]
            + ["-c", self.lan_conf_path]
            + ["-f", self.ipmisim_emu_path]
            + ["-s", self.emu_state_dir_path, "-n"]
        )

        logger.info("Starting agent: %s", " ".join(cmd))

        self.register_process(
            subprocess.Popen(cmd, stderr=subprocess.DEVNULL, close_fds=True)
        )

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_agent()

    def __str__(self):

        agent_info = (
            "\nipmi_sim lan: \n"
            "   Accessible at: {host}:{port} \n"
            "   User/Password:  {user}/{password}\n"
            "   Connected to guest VM at port: {vmport} \n"
        ).format(**self._ipmi_config)

        file_struct_info = (
            "\nipmi_sim files: \n"
            "   Sensor definitions file: {0.sensor_def_path}\n"
            "   Compiled sensors located in: {0.emu_state_dir_path}\n"
            "   Lan configurations: {0.lan_conf_path}\n"
            "   .emu commands file: {0.ipmisim_emu_path}\n"
        ).format(self)

        return ("\n" + "-" * 20 + "\n").join(
            (
                "IPMI simulator:",
                super(IPMIAgent, self).__str__(),
                file_struct_info + agent_info,
            )
        )
