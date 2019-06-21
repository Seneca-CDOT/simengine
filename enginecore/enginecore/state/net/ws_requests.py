"""Requests accepted by the ws_server

- ServerToClientRequests -> requests sent to the socket client
- ClientToServerRequests -> requests sent by the client to the server
"""
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
    # command status
    cmd_executed_status = 8
    # is sent when everything load power loop reaches the end
    load_loop_done = 9


class ClientToServerRequests(Enum):
    """Requests sent to the server by the ws client"""

    # == Asset Commands
    # toggle asset power
    set_power = 1
    # get overall system layout, status etc.
    get_sys_status = 2

    # == MISC
    # update UI layout
    set_layout = 10
    # update mains
    set_mains = 11
    # execute a play
    exec_play = 12
    # subscribe to system updates (such as power events, battery etc.)
    subscribe = 13
    # execute actions stored by recorder
    replay_actions = 14
    # set ambient
    set_ambient = 15
    # voltage update
    set_voltage = 16

    # == Recorder Requests
    # clear action history
    clear_actions = 20
    # get all/range of actions
    get_actions = 21
    # save/load actions from a file
    save_actions = 22
    load_actions = 23
    # toggle recorder status
    set_recorder_status = 24
    get_recorder_status = 25
    # execute random action
    exec_rand_actions = 26

    # == BMC-asset commands
    # set sensor status
    set_sensor_status = 40
    # cv replacement
    set_cv_replacement_status = 41
    # udpate controller states
    set_controller_status = 42
    # update physical drive details
    set_physical_drive_status = 43
