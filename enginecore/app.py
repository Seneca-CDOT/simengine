#!/usr/bin/env python3
""" Entry point """

import argparse
import os
import shutil
import tempfile

from enginecore.state.state_listener import StateListener
from enginecore.state.state_initializer import initialize


def configure_env(relative=False):
    """Set-up defaults for the env vars if not defined 
    (such as folder containing static .snmprec files, SHA of redis lua script) 
    """

    if relative:
        static_path = os.path.abspath("../data")
        ipmi_templ_path = os.path.abspath("./ipmi_template")
        lua_script_path = 'script/snmppub.lua'
    else:
        static_path = os.path.abspath("/usr/share/simengine/data")
        ipmi_templ_path = os.path.abspath("/usr/share/simengine/enginecore/ipmi_template")
        lua_script_path = '/usr/share/simengine/enginecore/script/snmppub.lua)'

    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', static_path)
    os.environ['SIMENGINE_IPMI_TEMPL'] = os.environ.get('SIMENGINE_IPMI_TEMPL', ipmi_templ_path)
    os.environ['SIMENGINE_SNMP_SHA'] = os.environ.get(
        'SIMENGINE_SNMP_SHA',
#        str(os.popen('/usr/local/bin/redis-cli script load "$(cat {})"'.format(lua_script_path)).read())
        str(os.popen('redis-cli script load "$(cat {})"'.format(lua_script_path)).read())
    )


def clear_temp():
    """All app data is stored in /tmp/simengine (which is cleared on restart)"""
    sys_temp = tempfile.gettempdir()
    simengine_temp = os.path.join(sys_temp, 'simengine')
    if os.path.exists(simengine_temp):
        for the_file in os.listdir(simengine_temp):
            file_path = os.path.join(simengine_temp, the_file)    
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
    else:
        os.makedirs(simengine_temp)

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

    # set-up temp app space
    clear_temp()

    # env space configuration
    configure_env(relative=args['develop'])

    # init state
    initialize(force_snmp_init=args['reload_data'])

    # run daemon
    StateListener(debug=args['verbose']).run()

if __name__ == '__main__':
    run()
