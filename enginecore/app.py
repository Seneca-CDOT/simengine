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
    
    os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', os.path.abspath("../data"))    
    initialize()

    # Subscribe to redis events
    StateListener().run()

if __name__ == '__main__':
    run()
