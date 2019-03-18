"""Requests  accepted by the ws_server"""
import enum


class ServerToClientRequests(enum.Enum):
    """Requests sent to the client """

    # asset updates (power, load etc.)
    asset = 1
    # ambient changes
    ambient = 2
    # system layout/topology
    topology = 3
    # wallpower status change
    mains = 4
    # list of plays
    plays = 5
    # list of actions
    action_list = 6
    # recorder status
    recorder_status = 7


class ClientToServerRequests(enum.Enum):
    """Requests sent to the server by the ws client"""

    # toggle power
    power = 1
    # update UI layout
    layout = 2
    # update mains
    mains = 3
    # execute a play
    play = 4
    # get status
    status = 5
    # subscribe to system updates
    subscribe = 6
    # execute actions stored by recorder
    replay_actions = 7
    # clear action history
    purge_actions = 8
    # get all/range of actions
    list_actions = 9
    # toggle recorder status
    set_recorder_status = 10
    get_recorder_status = 11
