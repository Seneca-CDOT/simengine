#!/usr/bin/env python3
""" Entry point """

from enginecore.state.state_listener import StateListener
from enginecore.state.state_initializer import initialize
import os

def run():
    """
    Initilize compnents' states in redis based on a reference model
    & launch event listener daemon
    """
    
    # configurationd
    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', os.path.abspath("../data"))
    os.environ['SIMENGINE_SNMP_SHA'] = os.environ.get(
        'SIMENGINE_SNMP_SHA', 
        str(os.popen('redis-cli script load "$(cat script/snmppub.lua)"').read())
    )

    # init state
    initialize()

    # run daemon
    StateListener().run()

if __name__ == '__main__':
    run()
