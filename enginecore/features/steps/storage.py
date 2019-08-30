# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import
import json
import os
import socket
from websocket import create_connection

from behave import given, when, then, step
from hamcrest import *


def _recvall(storcli64_socket):
    BUFF_SIZE = 4096  # 4 KiB
    data = b""
    while True:
        part = storcli64_socket.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


@then('response for asset "{key:d}" when running storcli64 command "{command}" is ok')
def step_impl(context, key, command):

    port = context.hardware[key].asset_info["storcliPort"]
    storcli64_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    storcli64_socket.connect(("0.0.0.0", port))
    storcli64_socket.send(json.dumps({"argv": command.split()}).encode())
    response = json.loads(str(_recvall(storcli64_socket).decode("utf-8")))
    assert_that(response["status"], is_(0))
    assert_that(response["stderr"], is_(""))
    assert_that(response["stdout"], not_none())

    storcli64_socket.close()
