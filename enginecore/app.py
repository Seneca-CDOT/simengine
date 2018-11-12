#!/usr/bin/python3
""" Entry point """

import argparse
import os
import sys
import logging

from enginecore.state.state_listener import StateListener

FORMAT = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"
DEV_FORMAT = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"


def configure_logger(develop=False):
    """Configure logger instance for the simengine app
    Args:
        develop(bool): indicates logger variant
    """

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(DEV_FORMAT, "%H:%M:%S" if develop else FORMAT)

    if develop:
        log_path = "info.log"
        stdout_h = logging.StreamHandler(sys.stdout)
        stdout_h.setFormatter(formatter)

        root.addHandler(stdout_h)
    else:
        log_path = os.path.join("var", "log", "simengine", "info.log")


    logfile_h = logging.FileHandler(log_path)
    logfile_h.setFormatter(formatter)
    root.addHandler(logfile_h)


def configure_env(relative=False):
    """Set-up defaults for the env vars if not defined 
    (such as folder containing static .snmprec files, SHA of redis lua script)

    Args:
        relative(bool): used for the development version, enables relative paths
    """

    if relative:
        static_path = os.path.abspath(os.path.join(os.pardir, "data"))
        ipmi_templ_path = os.path.abspath("ipmi_template")
        lua_script_path = os.path.join("script", "snmppub.lua")
    else:
        share_dir = os.path.join(os.sep, "usr", "share", "simengine")

        static_path = os.path.join(share_dir, "data")
        ipmi_templ_path = os.path.join(share_dir, "enginecore", "ipmi_template")
        lua_script_path = os.path.join(share_dir, "enginecore", "script", "snmppub.lua")

    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', static_path)
    os.environ['SIMENGINE_IPMI_TEMPL'] = os.environ.get('SIMENGINE_IPMI_TEMPL', ipmi_templ_path)
    os.environ['SIMENGINE_SNMP_SHA'] = os.environ.get(
        'SIMENGINE_SNMP_SHA',
        # str(os.popen('/usr/local/bin/redis-cli script load "$(cat {})"'.format(lua_script_path)).read())
        str(os.popen('redis-cli script load "$(cat {})"'.format(lua_script_path)).read())
    )


def run():
    """
    Initilize compnents' states in redis based on a reference model
    & launch event listener daemon
    """

    # parse cli option
    argparser = argparse.ArgumentParser(
        description='Start enginecore daemon running the main engine loop'
    )

    argparser.add_argument('-v', '--verbose', help="Enable State Listener Debugger", action='store_true')
    argparser.add_argument('-r', '--reload-data', help="Reload state data from .snmprec files", action='store_true')
    argparser.add_argument('-d', '--develop', help="Run in a development mode", action='store_true')

    args = vars(argparser.parse_args())

    # logging config
    configure_logger(develop=args['develop'])

    # env space configuration
    configure_env(relative=args['develop'])

    # run daemon
    StateListener(debug=args['verbose'], force_snmp_init=args['reload_data']).run()

if __name__ == '__main__':
    run()
