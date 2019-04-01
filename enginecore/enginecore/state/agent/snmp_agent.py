"""A wrapper for managing snmpsimd progoram 
"""

import subprocess
import os
import logging
import pwd
import grp
import tempfile
from enginecore.state.agent.agent import Agent


class SNMPAgent(Agent):
    """SNMP simulator """

    def __init__(
        self,
        key,
        host,
        port,
        public_community="public",
        private_community="private",
        lookup_oid="1.3.6",
    ):

        super(SNMPAgent, self).__init__()
        self._key_space_id = key

        # set up community strings
        self._snmp_rec_public_fname = public_community + ".snmprec"
        self._snmp_rec_private_fname = private_community + ".snmprec"

        sys_temp = tempfile.gettempdir()
        simengine_temp = os.path.join(sys_temp, "simengine")

        self._snmp_rec_dir = os.path.join(simengine_temp, str(key))
        os.makedirs(self._snmp_rec_dir)
        self._host = "{}:{}".format(host, port)

        # snmpsimd.py will be run by a user 'nobody'
        uid = pwd.getpwnam("nobody").pw_uid
        gid = grp.getgrnam("nobody").gr_gid

        # change ownership
        os.chown(self._snmp_rec_dir, uid, gid)
        snmp_rec_public_filepath = os.path.join(
            self._snmp_rec_dir, self._snmp_rec_public_fname
        )
        snmp_rec_private_filepath = os.path.join(
            self._snmp_rec_dir, self._snmp_rec_private_fname
        )

        # get location of the lua script that will be executed by snmpsimd
        redis_script_sha = os.environ.get("SIMENGINE_SNMP_SHA")
        snmpsim_config = "{}|:redis|key-spaces-id={},evalsha={}\n".format(
            lookup_oid, key, redis_script_sha
        )

        with open(snmp_rec_public_filepath, "a") as tmp_pub, open(
            snmp_rec_private_filepath, "a"
        ) as tmp_priv:
            tmp_pub.write(snmpsim_config)
            tmp_priv.write(snmpsim_config)

        self.start_agent()

        SNMPAgent.agent_num += 1

    def start_agent(self):
        """Logic for starting up the agent """

        log_file = os.path.join(self._snmp_rec_dir, "snmpsimd.log")

        cmd = [
            "snmpsimd.py",
            "--agent-udpv4-endpoint={}".format(self._host),
            "--variation-module-options=redis:host:127.0.0.1,port:6379,db:0,key-spaces-id:"
            + str(self._key_space_id),
            "--data-dir=" + self._snmp_rec_dir,
            "--transport-id-offset=" + str(SNMPAgent.agent_num),
            "--process-user=nobody",
            "--process-group=nobody",
            # "--daemonize",
            "--logging-method=file:" + log_file,
        ]

        logging.info("Starting agent: %s", " ".join(cmd))
        self.register_process(
            subprocess.Popen(cmd, stderr=subprocess.DEVNULL, close_fds=True)
        )
