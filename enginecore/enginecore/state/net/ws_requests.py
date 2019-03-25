"""Requests  accepted by the ws_server"""
from enum import Enum


class ServerToClientRequests(Enum):
    """Requests sent to the client """

    # asset updates (power, load etc.)
    asset_upd = 1
    # ambient changes
    ambient_upd = 2
    # system layout/topology
    sys_layout = 3
    # wallpower status change
    mains_upd = 4
    # list of plays
    play_list = 5
    # list of actions
    action_list = 6
    # recorder status
    recorder_status = 7


class ClientToServerRequests(Enum):
    """Requests sent to the server by the ws client"""

    # == Asset Commands
    # toggle asset power
    set_power = 1
    # get overall system layout, status etc.
    get_sys_status = 2

    # == MISC
    # update UI layout
    set_layout = 3
    # update mains
    set_mains = 4
    # execute a play
    exec_play = 5
    # subscribe to system updates (such as power events, battery etc.)
    subscribe = 6
    # execute actions stored by recorder
    replay_actions = 7
    # set ambient
    set_ambient = 8

    # == Recorder Requests
    # clear action history
    clear_actions = 9
    # get all/range of actions
    get_actions = 10
    # toggle recorder status
    set_recorder_status = 11
    get_recorder_status = 12

    # == BMC-asset commands
    # set sensor status
    set_sensor_status = 13
    # cv replacement
    set_cv_replacement_status = 14
    # udpate controller states
    set_controller_status = 15
    # update physical drive details
    set_physical_drive_status = 16
