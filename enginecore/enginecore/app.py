""" Entry point """

from state import StateListener, initialize


def run():
    """ Initilize compnents' states in redis based on reference model """
    initialize()
    """ Subscribe to redis events """
    StateListener().run()

if __name__ == '__main__':
    run()
 