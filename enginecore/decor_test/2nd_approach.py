# pylint: skip-file
import functools


class Db:

    action_names = []

    @classmethod
    def add_action(cls, action_name):
        """Save action to a database
        (making expensive I/O db call)
        """
        cls.action_names.append(action_name)

    @classmethod
    def get_all_actions(cls):
        """Retrieve all actions from a database
        (making expensive I/O db call0)
        """
        return cls.action_names

    @classmethod
    def record_action(cls, f):
        @functools.wraps(f)
        def record_wrapper(asset_self, *f_args, **f_kwargs):
            cls.add_action(f.__name__)
            return f(asset_self, *f_args, **f_kwargs)

        return record_wrapper


class Server:
    @Db.record_action
    def power_down(self):
        print("powering down")

    @Db.record_action
    def power_up(self):
        print("powering up")

    @Db.record_action
    def destroy_fan(self, fan_index):
        print("nuking fan #{}".format(fan_index))


def replay_all(server):
    [
        getattr(server, method_name).__wrapped__(server)
        for method_name in Db.get_all_actions()
    ]


server = Server()
server.power_down()

server = Server()
server.power_up()

server = Server()
server.destroy_fan(2)

print("== Replaying actions: ==")
server = Server()
replay_all(server)
