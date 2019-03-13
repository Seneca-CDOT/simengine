"""CLI endpoints for replaying, listing and managing recorded actions
"""
import argparse
from enginecore.state.api.state import StateClient


def range_args():
    """Get common action arguments"""

    common_args = argparse.ArgumentParser(add_help=False)

    common_args.add_argument(
        '-s', '--start', type=int, help="Starting at this action number (range specifier)"
    )

    common_args.add_argument(
        '-e', '--end', type=int, help="Ending at this action number (range specifier)"
    )

    return common_args


def actions_command(actions_group):
    """Action command can be used to manage/replay recorded actions performed by SimEngine users"""

    play_subp = actions_group.add_subparsers()
    
    replay_action = play_subp.add_parser('replay', help="Replay actions", parents=[range_args()])
    clear = play_subp.add_parser('clear', help="Purge action history", parents=[range_args()])


    # cli actions/callbacks

    replay_action.set_defaults(
        func=lambda args: StateClient.replay_actions(slice(args['start'], args['end']))
    )

    clear.set_defaults(
        func=lambda args: StateClient.clear_actions(slice(args['start'], args['end']))
    )
