"""CLI endpoints for replaying, listing and managing recorded actions
"""
import argparse
import sys
import os
import operator
from datetime import datetime as dt
from enginecore.state.net.state_client import StateClient
from enginecore.tools.recorder import Recorder


def print_action_list(action_details):
    """Display action history"""

    if not action_details:
        print("Action history is empty or the range specifier is invalid!")
        return

    for action in action_details:
        print(
            "{number}) [{time}] {work}".format(
                **action, time=dt.fromtimestamp(action["timestamp"])
            )
        )


def try_date_format(date_str, date_format):
    """Try to apply a specific date format
    Args:
        date_str: date to be parsed
        date_format: will be applied to date_str
    """
    try:
        return dt.strptime(date_str, date_format)
    except ValueError:
        return None


def get_date_from_str(date_str):
    """CLI either accepts today's time as 17:35:38 or full date as 2019-04-11 17:35:38
    Args:
        date_str: provided date to be parsed
    Returns:
        None if parsing failed, else parsed date
    """

    parsed_date = try_date_format(date_str, "%H:%M:%S")
    if parsed_date:
        parsed_date = dt.combine(dt.now(), parsed_date.time())
    else:
        parsed_date = try_date_format(date_str, "%Y-%m-%d %H:%M:%S")

    return parsed_date


def get_index_from_range_opt(range_opt, actions, start_opt=True):
    """Analyze range option, find index for rand_opt if it is a date string
    Args:
        rand_opt: either index of an action or date string in format 
                  "%H:%M:%S" or "%Y-%m-%d %H:%M:%S"
        actions(list): list of action history
        start_opt: indicates if the index provided is the starting point of a slice
    Returns:
        int: index of the starting or ending action
    """

    # action index was provided - return number
    if range_opt is None or range_opt.isdigit():
        return int(range_opt) if range_opt else None

    # try to parse a date
    range_date = get_date_from_str(range_opt)
    if not range_date:
        return None

    # find actions within the date range
    filter_actions_by_date = lambda d, op: list(
        filter(lambda x: op(dt.fromtimestamp(x["timestamp"]), d), actions)
    )
    filtered_actions = filter_actions_by_date(
        range_date, operator.ge if start_opt else operator.le
    )

    if not filtered_actions:
        return None

    border_date_action = (min if start_opt else max)(
        filtered_actions, key=lambda x: x["number"]
    )
    range_idx = border_date_action["number"] if border_date_action else None

    if not start_opt and range_idx is not None:
        range_idx = range_idx + 1

    return range_idx


def get_action_slice(start, end):
    """Parse start & end range specifiers
    Args:
        start: start index or starting datestring or time string
                in a format "%H:%M:%S" or "%Y-%m-%d %H:%M:%S"
        end: end index or end date/time in a format "%H:%M:%S" or "%Y-%m-%d %H:%M:%S"
    Returns:
        slice: range of actions
    """

    try:
        return slice(int(start), int(end))
    except (ValueError, TypeError):

        # attemp to parse dates if one/both of the range options are non digits
        all_actions = StateClient.list_actions(slice(None, None))

        start = get_index_from_range_opt(start, all_actions)
        end = get_index_from_range_opt(end, all_actions, start_opt=False)

        return slice(start, end)


def dry_run_actions(args):
    """Do a dry run of action replay without changing of affecting assets' states"""
    action_slc = get_action_slice(args["start"], args["end"])
    action_details = StateClient.list_actions(action_slc)
    try:
        Recorder.perform_dry_run(action_details, action_slc)
    except KeyboardInterrupt:
        print("Dry-run was interrupted by the user", file=sys.stderr)


def range_args():
    """Get common action arguments"""

    common_args = argparse.ArgumentParser(add_help=False)

    common_args.add_argument(
        "-s",
        "--start",
        help="Starting at this action number, or at this time today \
            (format %%H:%%M:%%S) or date (%%Y-%%m-%%d %%H:%%M:%%S)",
    )

    common_args.add_argument(
        "-e",
        "--end",
        help="Ending at this action number, or at this time today \
            (format %%H:%%M:%%S) or date (%%Y-%%m-%%d %%H:%%M:%%S)",
    )

    return common_args


def handle_file_command(args, client_request_func):
    """Process file command (either save or load)
    Args:
        client_request_func(callable): StateClient method processing file command
    """
    client_request_func(
        os.path.abspath(os.path.expanduser(args["filename"])),
        get_action_slice(args["start"], args["end"]),
    )


def actions_command(actions_group):
    """Action command can be used to manage/replay recorded
    actions performed by SimEngine users"""

    play_subp = actions_group.add_subparsers()

    # replay commands
    replay_action = play_subp.add_parser(
        "replay",
        help="Replay actions, will replay all history if range is not provided",
        parents=[range_args()],
    )
    replay_action.add_argument(
        "-l", "--list", action="store_true", help="List re-played actions"
    )

    #  clear action history
    clear_action = play_subp.add_parser(
        "clear", help="Purge action history", parents=[range_args()]
    )
    clear_action.add_argument(
        "-l", "--list", action="store_true", help="List deleted actions"
    )

    # misc
    disable_action = play_subp.add_parser(
        "disable", help="Disable recorder (recorder will ignore incoming commands)"
    )
    enable_action = play_subp.add_parser(
        "enable", help="Enable recorder registering incoming actions"
    )
    status_action = play_subp.add_parser(
        "status",
        help="Returns recorder status indicating if recorder is enabled \
            and if it is in-process of replaying",
    )
    list_action = play_subp.add_parser(
        "list", help="List action history", parents=[range_args()]
    )
    dry_run_action = play_subp.add_parser(
        "dry-run", help="Perform a dry run of actions replay", parents=[range_args()]
    )

    save_action = play_subp.add_parser(
        "save", help="Save action history to a file", parents=[range_args()]
    )

    save_action.add_argument(
        "-l", "--list", action="store_true", help="Explicitly list saved actions"
    )

    save_action.add_argument(
        "-f", "--filename", type=str, required=True, help="Target file name"
    )

    load_action = play_subp.add_parser(
        "load",
        help="Load action history from a file (will override the existing actions)",
        parents=[range_args()],
    )

    load_action.add_argument(
        "-f", "--filename", type=str, required=True, help="Will load from this file"
    )

    rand_action = play_subp.add_parser(
        "random", help="Perform random actions associated with assets"
    )
    rand_action.add_argument(
        "-c", "--count", type=int, help="Number of actions to be performed", default=1
    )
    rand_action.add_argument(
        "-k",
        "--asset-keys",
        nargs="+",
        type=int,
        help="Include only these assets when picking a random component,\
            defaults to all if not provided",
    )
    rand_action.add_argument(
        "-s",
        "--seconds",
        type=int,
        help="Perform actions for 'n' seconds (alternative to 'count')",
    )
    rand_action.add_argument(
        "-n",
        "--nap-time",
        type=float,
        help="Pause between each random action or max nap time if --min-nap is present",
    )

    rand_action.add_argument(
        "-m",
        "--min-nap",
        type=float,
        help="Minimum sleep time, pauses between actions will be set to random\
            if this value is provided",
    )

    # cli actions/callbacks
    replay_action.set_defaults(
        func=lambda args: [
            print_action_list(
                StateClient.list_actions(get_action_slice(args["start"], args["end"]))
            )
            if args["list"]
            else None,
            StateClient.replay_actions(get_action_slice(args["start"], args["end"])),
        ]
    )

    clear_action.set_defaults(
        func=lambda args: [
            print_action_list(
                StateClient.list_actions(get_action_slice(args["start"], args["end"]))
            )
            if args["list"]
            else None,
            StateClient.clear_actions(get_action_slice(args["start"], args["end"])),
        ]
    )

    list_action.set_defaults(
        func=lambda args: print_action_list(
            StateClient.list_actions(get_action_slice(args["start"], args["end"]))
        )
    )

    disable_action.set_defaults(
        func=lambda _: StateClient.set_recorder_status(enabled=False)
    )

    enable_action.set_defaults(
        func=lambda _: StateClient.set_recorder_status(enabled=True)
    )
    status_action.set_defaults(
        func=lambda _: print(
            "Enabled: {enabled}\nReplaying: {replaying}".format(
                **StateClient.get_recorder_status()
            )
        )
    )
    dry_run_action.set_defaults(func=dry_run_actions)

    save_action.set_defaults(
        func=lambda args: handle_file_command(args, StateClient.save_actions)
    )
    load_action.set_defaults(
        func=lambda args: handle_file_command(args, StateClient.load_actions)
    )

    rand_action.set_defaults(func=StateClient.rand_actions)
