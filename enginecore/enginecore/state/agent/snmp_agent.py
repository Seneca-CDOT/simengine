"""A wrapper for managing snmpsimd progoram 
"""

import subprocess
import os
import logging
import pwd
import grp
from enginecore.state.agent.agent import Agent

logger = logging.getLogger(__name__)


class SNMPAgent(Agent):
    """SNMP simulator/wrapper for snmpsimd.py process;
    initializes data/work environment for snmpsimd.py with redis variation module
    and manages simulator instance.
    """

    def __init__(self, asset_key, snmp_conf):
        super(SNMPAgent, self).__init__()

        self._asset_key = asset_key
        self._snmp_conf = snmp_conf

        self._init_agent_environment()
        self._init_snmprec_files()

        self.start_agent()

    def _init_agent_environment(self):
        """Initialize temp work environment of the agent
        Update ownership since snmpsimd.py will be run by user 'nobody'"""

        self._snmp_rec_dir = os.path.join(
            self._snmp_conf["work_dir"], str(self._asset_key)
        )

        if not os.path.exists(self._snmp_rec_dir):
            os.makedirs(self._snmp_rec_dir)

        if os.getuid() == 0:
            uid = pwd.getpwnam("nobody").pw_uid
            gid = grp.getgrnam("nobody").gr_gid

            os.chown(self._snmp_rec_dir, uid, gid)

    def _init_snmprec_files(self):
        """Initialize data files for public/private SNMP communities
        (files pointing to redis key-spaces for snmp devices)
        """

        # initialize community strings & lookup depth
        rec_public_path = os.path.join(self._snmp_rec_dir, "public.snmprec")
        rec_private_path = os.path.join(self._snmp_rec_dir, "private.snmprec")
        lookup_oid = (
            self._snmp_conf["lookup_oid"]
            if "lookup_oid" in self._snmp_conf
            else "1.3.6"
        )

        # get location of the lua script that will be executed by snmpsimd
        redis_script_sha = os.environ.get("SIMENGINE_SNMP_SHA")
        snmpsim_config = "{}|:redis|key-spaces-id={},evalsha={}\n".format(
            lookup_oid, self._asset_key, redis_script_sha
        )

        with open(rec_public_path, "a") as pub:
            pub.write(snmpsim_config)

        with open(rec_private_path, "a") as priv:
            priv.write(snmpsim_config)

    def start_agent(self):
        """Logic for starting up the agent """

        # TODO: get redis port/host from config
        var_opt = "redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:" + str(
            self._asset_key
        )

        cmd = [
            "snmpsimd.py",
            "--agent-udpv4-endpoint={host}:{port}".format(**self._snmp_conf),
            "--variation-module-options=" + var_opt,
            # The --data-dir option breaks python 3 compatibility
            #"--data-dir=" + self._snmp_rec_dir,
            "--cache-dir=" + self._snmp_rec_dir,
            "--transport-id-offset=" + str(SNMPAgent.agent_num),
            # "--daemonize",
            "--logging-method=file:" + self.log_path,
            "--cache-dir",
            self._snmp_rec_dir,
        ]

        if os.getuid() == 0:
            cmd.extend(["--process-user=nobody", "--process-group=nobody"])

        logger.info("Starting agent: %s", " ".join(cmd))
        self.register_process(
            subprocess.Popen(cmd, stderr=subprocess.DEVNULL, close_fds=True)
        )

    @property
    def log_path(self):
        """Path to snmpsim log file"""
        return os.path.join(self._snmp_rec_dir, "snmpsimd.log")

    def __str__(self):

        file_struct_info = (
            "\n" "   Data directory: {0._snmp_rec_dir}\n" "   Log file: {0.log_path} \n"
        ).format(self)
        agent_info = ("   Accessible at: {host}:{port} \n").format(**self._snmp_conf)

        return ("\n" + "-" * 20 + "\n").join(
            (
                "SNMP simulator:",
                super(SNMPAgent, self).__str__(),
                file_struct_info + agent_info,
            )
        )
