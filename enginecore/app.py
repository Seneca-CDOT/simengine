#!/usr/bin/env python3
""" Entry point """

import argparse
import os

from enginecore.state.state_listener import StateListener
from enginecore.state.state_initializer import initialize

def configure_env():
    """Set-up defaults for the env vars if not defined 
    (such as folder containing static .snmprec files, SHA of redis lua script) 
    """
#    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', os.path.abspath("../data"))
    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', os.path.abspath("/usr/share/simengine/data"))
#    os.environ['SIMENGINE_IPMI_TEMPL'] = os.environ.get('SIMENGINE_IPMI_TEMPL', os.path.abspath("./ipmi_template"))
    os.environ['SIMENGINE_IPMI_TEMPL'] = os.environ.get('SIMENGINE_IPMI_TEMPL', os.path.abspath("/usr/share/simengine/enginecore/ipmi_template"))
    os.environ['SIMENGINE_SNMP_SHA'] = os.environ.get(
        'SIMENGINE_SNMP_SHA', 
#        str(os.popen('redis-cli script load "$(cat script/snmppub.lua)"').read())
        str(os.popen('redis-cli script load "$(cat /usr/share/simengine/enginecore/script/snmppub.lua)"').read())
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

    argparser.add_argument('-d', '--debug', help="Enable State Listener Debugger", action='store_true')
    argparser.add_argument('-r', '--reload-data', help="Reload state data from .snmprec files", action='store_true')

    args = vars(argparser.parse_args())

    # env space configuration
    configure_env()

    # init state
    initialize(force_snmp_init=args['reload_data'])

    # run daemon
    StateListener(debug=args['debug']).run()

if __name__ == '__main__':
    run()
