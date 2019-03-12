"""CLI endpoints for managing and executing playback related commands
"""
import os 
from enginecore.state.api.state import StateClient


def actions_command(actions_group):

    play_subp = actions_group.add_subparsers()
    
    replay_action = play_subp.add_parser('replay', help="Replay actions")
    replay_action.add_argument(
        '-a',
        '--all',
        required=True,
        help="Replay all actions stored in recorder history",
        action='store_true'
    )

    clear = play_subp.add_parser('clear', help="Purge action history")

    # cli actions/callbacks
    replay_action.set_defaults(
        func=lambda args: StateClient.replay_all()
    )

    clear.set_defaults(
        func=lambda args: StateClient.clear_actions()
    )
