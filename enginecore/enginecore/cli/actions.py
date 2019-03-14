"""CLI endpoints for replaying, listing and managing recorded actions
"""
import argparse
from enginecore.state.api.state import StateClient


def print_action_list(action_details):
    """Display action history"""

    if not action_details:
        print("Action history is empty or the range specifier is invalid!")
        return

    for action in action_details:
        print("{number}) [{timestamp}] {work}".format(**action))


def range_args():
    """Get common action arguments"""

    common_args = argparse.ArgumentParser(add_help=False)

    common_args.add_argument(
        "-s",
        "--start",
        type=int,
        help="Starting at this action number (range specifier)",
    )

    common_args.add_argument(
        "-e", "--end", type=int, help="Ending at this action number (range specifier)"
    )

    return common_args


def actions_command(actions_group):
    """Action command can be used to manage/replay recorded actions performed by SimEngine users"""

    play_subp = actions_group.add_subparsers()

    replay_action = play_subp.add_parser(
        "replay",
        help="Replay actions, will replay all history if range is not provided",
        parents=[range_args()],
    )
    replay_action.add_argument(
        "-l", "--list", action="store_true", help="List re-played actions"
    )
    clear_action = play_subp.add_parser(
        "clear", help="Purge action history", parents=[range_args()]
    )
    clear_action.add_argument(
        "-l", "--list", action="store_true", help="List deleted actions"
    )
    list_action = play_subp.add_parser(
        "list", help="List action history", parents=[range_args()]
    )

    # cli actions/callbacks

    replay_action.set_defaults(
        func=lambda args: [
            print_action_list(
                StateClient.list_actions(slice(args["start"], args["end"]))
            )
            if args["list"]
            else None,
            StateClient.replay_actions(slice(args["start"], args["end"])),
        ]
    )

    clear_action.set_defaults(
        func=lambda args: [
            print_action_list(
                StateClient.list_actions(slice(args["start"], args["end"]))
            )
            if args["list"]
            else None,
            StateClient.clear_actions(slice(args["start"], args["end"])),
        ]
    )

    list_action.set_defaults(
        func=lambda args: print_action_list(
            StateClient.list_actions(slice(args["start"], args["end"]))
        )
    )
