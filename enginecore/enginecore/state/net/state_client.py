import json
import os
from websocket import create_connection
from enginecore.state.net.ws_requests import ClientToServerRequests


class StateClient:
    """A web-socket client responsible for state"""

    socket_conf = {
        "host": os.environ.get("SIMENGINE_SOCKET_HOST", "0.0.0.0"),
        "port": os.environ.get("SIMENGINE_SOCKET_PORT", int(8000)),
    }

    def __init__(self, key):
        self._asset_key = key
        self._ws_client = StateClient.get_ws_client()

    @classmethod
    def get_ws_client(cls):
        return create_connection(
            "ws://{host}:{port}/simengine".format(**StateClient.socket_conf)
        )

    @classmethod
    def send_request(cls, request, data={}, ws_client=None):
        """Send request to the simengine websocket server"""
        if not ws_client:
            ws_client = StateClient.get_ws_client()

        ws_client.send(json.dumps({"request": request.name, "payload": data}))

    def power_up(self):
        StateClient.send_request(
            ClientToServerRequests.power,
            {"status": 1, "key": self._asset_key},
            self._ws_client,
        )

    def _state_off(self, hard=False):
        StateClient.send_request(
            ClientToServerRequests.power,
            {"status": 0, "key": self._asset_key, "hard": hard},
            self._ws_client,
        )

    def shut_down(self):
        """Graceful shutdown"""
        self._state_off()

    def power_off(self):
        """Abrupt shut off"""
        self._state_off(hard=True)

    @classmethod
    def power_outage(cls):
        """Simulate complete power outage/restoration"""
        StateClient.send_request(ClientToServerRequests.mains, {"mains": 0})

    @classmethod
    def power_restore(cls):
        """Simulate complete power restoration"""
        StateClient.send_request(ClientToServerRequests.mains, {"mains": 1})

    @classmethod
    def replay_actions(cls, slc=slice(None, None)):
        StateClient.send_request(
            ClientToServerRequests.replay_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def clear_actions(cls, slc=slice(None, None)):
        StateClient.send_request(
            ClientToServerRequests.purge_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def list_actions(cls, slc=slice(None, None)):

        ws_client = StateClient.get_ws_client()

        StateClient.send_request(
            ClientToServerRequests.list_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
            ws_client=ws_client,
        )

        return json.loads(ws_client.recv())["payload"]["actions"]

    @classmethod
    def set_recorder_status(cls, enabled):
        """Toggle recorder status"""
        StateClient.send_request(
            ClientToServerRequests.set_recorder_status, {"enabled": enabled}
        )

    @classmethod
    def get_recorder_status(cls):
        """Retrieve recorder status"""
        ws_client = StateClient.get_ws_client()

        StateClient.send_request(
            ClientToServerRequests.get_recorder_status, ws_client=ws_client
        )

        return json.loads(ws_client.recv())["payload"]["status"]

    @classmethod
    def set_sensor_status(cls, asset_key, sensor_name, sensor_value):
        """Update runtime BMC sensor value"""
        StateClient.send_request(
            ClientToServerRequests.sensor,
            {
                "key": asset_key,
                "sensor_name": sensor_name,
                "sensor_value": sensor_value,
            },
        )

    @classmethod
    def set_cv_replacement(cls, asset_key, controller, repl_status, wt_on_fail):
        StateClient.send_request(
            ClientToServerRequests.cv_replacement_status,
            {
                "key": asset_key,
                "controller": controller,
                "repl_status": repl_status,
                "wt_on_fail": wt_on_fail,
            },
        )
