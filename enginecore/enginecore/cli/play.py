"""CLI endpoints for managing and executing playback related commands
"""
import os
from enginecore.state.api import IStateManager


def display_plays(plays):
    """Show a list of available scenarios"""

    show_scripts_of_type = lambda t, p: print("{}:\n {}".format(t, "\n ".join(p)))

    show_scripts_of_type("Bash Scripts", plays[0])
    show_scripts_of_type("Python Scripts", plays[1])


def play_command(power_group):
    """CLI endpoints for managing assets' power states & wallpower"""
    play_subp = power_group.add_subparsers()

    folder_action = play_subp.add_parser(
        "folder", help="Update user-defined script folder"
    )
    folder_action.add_argument(
        "-p",
        "--path",
        type=str,
        required=True,
        help="Path to the folder containing playback scripts",
    )

    list_action = play_subp.add_parser(
        "list", help="List scripts available for execution"
    )
    exec_action = play_subp.add_parser("execute", help="Execute a specific script")
    exec_action.add_argument(
        "-p", "--play", type=str, required=True, help="Name of the play to be executed"
    )

    # cli actions/callbacks
    folder_action.set_defaults(
        func=lambda args: IStateManager.set_play_path(
            os.path.abspath(os.path.expanduser(args["path"]))
        )
    )

    list_action.set_defaults(func=lambda args: display_plays(IStateManager.plays()))

    exec_action.set_defaults(
        func=lambda args: IStateManager.execute_play(
            args["play"]
        )  # TODO: handle invalid play
    )
