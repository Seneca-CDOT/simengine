""" Entry point """

from enginecore.state.state_listener import StateListener
from enginecore.state.state_initializer import initialize

def run():
    """
    Initilize compnents' states in redis based on a reference model
    & launch event listener daemon
    """
    initialize()

    # Subscribe to redis events
    StateListener().run()

if __name__ == '__main__':
    run()
