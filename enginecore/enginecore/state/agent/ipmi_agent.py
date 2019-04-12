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


class IPMIAgent(Agent):
    """Python wrapper around ipmi_sim program"""

    supported_sensors = dict.fromkeys(SUPPORTED_SENSORS, "")
    lan_conf_attributes = [
        "host",
        "port",
        "user",
        "password",
        "vmport",
        "num_components",
    ]

    def __init__(self, ipmi_dir, ipmi_config, sensor_repo):
        super(IPMIAgent, self).__init__()

        self._ipmi_dir = ipmi_dir
        self._sensor_repo = sensor_repo
        self._init_ipmi_dir()

        # sensor, emu & lan configuration file paths

        # Template options
        lan_conf_opt = {
            "asset_key": self._sensor_repo.server_key,
            "extend_lib": self.extend_plugin_path,
            **ipmi_config,
        }

        ipmisim_emu_opt = {"ipmi_dir": self._ipmi_dir, **IPMIAgent.supported_sensors}

        main_sdr_opt = {
            "ipmi_dir": self._ipmi_dir,
            "includes": "",
            **IPMIAgent.supported_sensors,
        }

        # initialize sensors
        for i, sensor_name in enumerate(sensor_repo.sensors):

            sensor = sensor_repo.sensors[sensor_name]

            # pp(sensor)
            s_specs = sensor.specs
            # pp(s_specs)

            s_idx = sensor.address

            sensor_file = s_specs["name"]

            index = str(s_specs["index"] + 1) if "index" in s_specs else ""

            main_sdr_opt[s_specs["type"]] += 'define IDX "{}" \n'.format(index)

            main_sdr_opt[s_specs["type"]] += 'define ID_STR "{}" \n'.format(i)
            main_sdr_opt[s_specs["type"]] += 'define ADDR "{}" \n'.format(s_idx)

            main_sdr_opt[s_specs["type"]] += 'define LNR "{}"  \n'.format(
                s_specs["lnr"] if "lnr" in s_specs else 0
            )
            main_sdr_opt[s_specs["type"]] += 'define LCR "{}"  \n'.format(
                s_specs["lcr"] if "lcr" in s_specs else 0
            )
            main_sdr_opt[s_specs["type"]] += 'define LNC "{}"  \n'.format(
                s_specs["lnc"] if "lnc" in s_specs else 0
            )
            main_sdr_opt[s_specs["type"]] += 'define UNC "{}"  \n'.format(
                s_specs["unc"] if "unc" in s_specs else 0
            )
            main_sdr_opt[s_specs["type"]] += 'define UCR "{}"  \n'.format(
                s_specs["ucr"] if "ucr" in s_specs else 0
            )
            main_sdr_opt[s_specs["type"]] += 'define UNR "{}"  \n'.format(
                s_specs["unr"] if "unr" in s_specs else 0
            )

            # Specify if sensor values should be returned:
            main_sdr_opt[s_specs["type"]] += 'define R_LNR "{}"  \n'.format(
                "lnr" in s_specs
            )
            main_sdr_opt[s_specs["type"]] += 'define R_LCR "{}"  \n'.format(
                "lcr" in s_specs
            )
            main_sdr_opt[s_specs["type"]] += 'define R_LNC "{}"  \n'.format(
                "lnc" in s_specs
            )
            main_sdr_opt[s_specs["type"]] += 'define R_UNC "{}"  \n'.format(
                "unc" in s_specs
            )
            main_sdr_opt[s_specs["type"]] += 'define R_UCR "{}"  \n'.format(
                "ucr" in s_specs
            )
            main_sdr_opt[s_specs["type"]] += 'define R_UNR "{}"  \n'.format(
                "unr" in s_specs
            )

            # s_name = s_specs['name'].format(index='"$IDX"')

            main_sdr_opt[s_specs["type"]] += 'define C_NAME "{}" \n'.format(
                s_specs["name"]
            )
            main_sdr_opt[s_specs["type"]] += 'include "{}/{}.sdrs" \n'.format(
                self._ipmi_dir, s_specs["type"]
            )

            #  0x20  0   0x74    3     1
            e_type = s_specs["eventReadingType"] if "eventReadingType" in s_specs else 1
            s_idx_2 = 8 if "eventReadingType" in s_specs else 3

            ipmisim_emu_opt[
                s_specs["type"]
            ] += "sensor_add 0x20  0   {}   {}     {} poll 2000 ".format(
                s_idx, s_idx_2, e_type
            )
            ipmisim_emu_opt[
                s_specs["type"]
            ] += 'file $TEMP_IPMI_DIR"/sensor_dir/{}" \n'.format(sensor_file)

        # Set server-specific includes
        if ipmi_config["num_components"] == 2:
            ipmisim_emu_opt["includes"] = 'include "{}"'.format(
                os.path.join(self._ipmi_dir, "ipmisim1_psu.emu")
            )
            main_sdr_opt["includes"] = 'include "{}"'.format(
                os.path.join(self._ipmi_dir, "main_dual_psu.sdrs")
            )

        # Substitute a template
        self._substitute_template_file(self.lan_conf_path, lan_conf_opt)
        self._substitute_template_file(self.ipmisim_emu_path, ipmisim_emu_opt)
        self._substitute_template_file(self.sensor_def_path, main_sdr_opt)

        self._compile_sensors()
        self._update_permissions()

        self.start_agent()

        IPMIAgent.agent_num += 1

    def _substitute_template_file(self, filename, options):
        """Update file using python templating """
        with open(filename, "r+", encoding="utf-8") as filein:
            template = Template(filein.read())
            filein.seek(0)
            filein.write(template.substitute(options))

    def _populate_template_files(self, lan_conf_opt, ipmisim_emu_opt, main_sdr_opt):
        pass

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

        logging.info("Starting agent: %s", " ".join(cmd))

        self.register_process(
            subprocess.Popen(cmd, stderr=subprocess.DEVNULL, close_fds=True)
        )

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_agent()
