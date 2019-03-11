# pylint: disable=E0402


import time
from server import Server 
from recorder import Recorder

if __name__ == '__main__':
    recorder = Recorder()


    server = Server()
    server.recorder = recorder
    server.power_down() # <-takes 1 second

    time.sleep(5)
    server.power_up()
    server.destroy_fan(3)


    print('== Replaying actions: ==')
    recorder.replay_all()

    play_last_2 = slice(-2, None)
    # recorder.replay_range(play_last_2)
