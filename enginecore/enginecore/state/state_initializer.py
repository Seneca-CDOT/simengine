"""Initialize redis state based on reference model """
import os
import subprocess
import tempfile
import shutil

import redis

from enginecore.model.graph_reference import GraphReference
from enginecore.tools.utils import format_as_redis_key


def get_temp_workplace_dir():
    """Get location of the temp directory"""
    sys_temp = tempfile.gettempdir()
    sim_temp = os.environ["SIMENGINE_WORKPLACE_TEMP"] = os.environ.get(
        "SIMENGINE_WORKPLACE_TEMP", "simengine"
    )
    simengine_temp = os.path.join(sys_temp, sim_temp)
    return simengine_temp


def configure_env(relative=False):
    """Set-up defaults for the env vars if not defined 
    (such as folder containing static .snmprec files, SHA of redis lua script)

    Args:
        relative(bool): used for the development version, enables relative paths
    """

    if relative:
        static_path = os.path.abspath(os.path.join(os.pardir, "data"))
        ipmi_templ_path = os.path.abspath("ipmi_template")
        storcli_templ_path = os.path.abspath("storcli_template")
        lua_script_path = os.path.join("script", "snmppub.lua")
    else:
        share_dir = os.path.join(os.sep, "usr", "share", "simengine")
        static_path = os.path.join(share_dir, "data")
        ipmi_templ_path = os.path.join(share_dir, "enginecore", "ipmi_template")
        storcli_templ_path = os.path.join(share_dir, "enginecore", "storcli_template")
        lua_script_path = os.path.join(share_dir, "enginecore", "script", "snmppub.lua")

    os.environ["SIMENGINE_STATIC_DATA"] = os.environ.get(
        "SIMENGINE_STATIC_DATA", static_path
    )
    os.environ["SIMENGINE_IPMI_TEMPL"] = os.environ.get(
        "SIMENGINE_IPMI_TEMPL", ipmi_templ_path
    )
    os.environ["SIMENGINE_STORCLI_TEMPL"] = os.environ.get(
        "SIMENGINE_STORCLI_TEMPL", storcli_templ_path
    )
    os.environ["SIMENGINE_SOCKET_HOST"] = os.environ.get(
        "SIMENGINE_SOCKET_HOST", "0.0.0.0"
    )
    os.environ["SIMENGINE_SOCKET_PORT"] = os.environ.get(
        "SIMENGINE_SOCKET_PORT", str(8000)
    )

    os.environ["SIMENGINE_REDIS_HOST"] = os.environ.get(
        "SIMENGINE_REDIS_HOST", "0.0.0.0"
    )
    os.environ["SIMENGINE_REDIS_PORT"] = os.environ.get(
        "SIMENGINE_REDIS_PORT", str(6379)
    )

    os.environ["SIMENGINE_SNMP_SHA"] = os.environ.get(
        "SIMENGINE_SNMP_SHA",
        # str(os.popen('/usr/local/bin/redis-cli script load "$(cat {})"'
        # .format(lua_script_path)).read())
        subprocess.check_output(
            'redis-cli script load "$(cat {})"'.format(lua_script_path), shell=True
        ).decode("utf-8"),
    )


def clear_temp():
    """All app data is stored in /tmp/simengine (which is cleared on restart)"""
    simengine_temp = get_temp_workplace_dir()
    if os.path.exists(simengine_temp):
        for the_file in os.listdir(simengine_temp):
            file_path = os.path.join(simengine_temp, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
    else:
        os.makedirs(simengine_temp)


def initialize(force_snmp_init=False):
    """ Initialize redis state using topology defined in the graph db """

    graph_ref = GraphReference()
    redis_store = redis.StrictRedis(host="localhost", port=6379)

    with graph_ref.get_session() as session:
        results = session.run(
            """
            MATCH (asset:Asset) OPTIONAL MATCH (asset:Asset)-[:HAS_OID]->(oid)
            return asset, collect(oid) as oids
            """
        )

    for record in results:
        asset_type = record["asset"].get("type")
        asset_key = str(record["asset"].get("key"))

        init_from_snmprec = (
            not redis_store.exists("{}-{}:state".format(asset_key, asset_type))
        ) or force_snmp_init
        redis_store.set("{}-{}:state".format(asset_key, asset_type), 1)
        formatted_key = asset_key.zfill(10)
        temp_ordering_key = formatted_key + "-temp_oids_ordering"

        graph_oids = {}
        for oid in record["oids"]:  # loop over oids that are defined in the graph db
            graph_oids[oid.get("OID")] = {
                "dtype": oid.get("dataType"),
                "value": oid.get("defaultValue"),
            }

        # Set-up in the SNMPSim format
        if "SNMPSim" in record["asset"].labels and record["oids"] and init_from_snmprec:

            # Read a file containing static .snmprec data
            static_oid_file = record["asset"].get("staticOidFile")
            static_oid_path = os.path.join(
                os.environ.get("SIMENGINE_STATIC_DATA"), static_oid_file
            )

            with open(static_oid_path, "r") as sfile_handler:
                for line in sfile_handler:

                    oid, dtype, value = line.replace("\n", "").split("|")
                    if oid in graph_oids:
                        dtype = graph_oids[oid]["dtype"]
                        value = graph_oids[oid]["value"]

                    key_and_oid = format_as_redis_key(formatted_key, oid)
                    redis_store.lpush(temp_ordering_key, key_and_oid)
                    redis_store.set(key_and_oid, "{}|{}".format(dtype, value))

            redis_store.sort(
                temp_ordering_key, store=formatted_key + "-oids_ordering", alpha=True
            )
            redis_store.delete(temp_ordering_key)
            redis_store.rpush(asset_key, formatted_key)


if __name__ == "__main__":
    initialize()
