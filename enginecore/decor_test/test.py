# pylint: skip-file

import functools


class Recorder:


    def __init__(self):
        self._actions = []

    def __call__(self, f):
        @functools.wraps(f)
        def record_wrapper(asset_self, *f_args, **f_kwargs):
            self._actions.append(functools.partial(f, asset_self, *f_args, **f_kwargs))
            
            return f(asset_self, *f_args, **f_kwargs)
        return record_wrapper

    def replay_all(self):
        self.replay_range(slice(None, None))

    def replay_range(self, slc):
        [a() for a in self._actions[slc]]



recorder = Recorder()

class Server:

    @recorder
    def power_down(self):
        print('powering down')

    @recorder
    def power_up(self):
        print('powering up')

    @recorder
    def destroy_fan(self, fan_index):
        print('nuking fan #{}'.format(fan_index))


server = Server()
# server.power_down()
# server.power_up()
server.power_down()
server.destroy_fan(3)


print('== Replaying actions: ==')
recorder.replay_all()
# recorder.replay_range(slice(-2, None))
