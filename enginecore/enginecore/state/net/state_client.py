"""SimEngine web socket server client interface
This client can be used to communicate recordable commands to the simengine websocket;
"""

import json
import os
from websocket import create_connection
from enginecore.state.net.ws_requests import ClientToServerRequests


class StateClient:
    """A web-socket client responsible for state"""

    socket_conf = {
        "host": os.environ.get("SIMENGINE_SOCKET_HOST", "0.0.0.0"),
        "port": os.environ.get("SIMENGINE_SOCKET_PORT", int(8000)),
        "path": os.environ.get("SIMENGINE_SOCKET_PATH", "simengine"),
    }

    def __init__(self, key: str):
        self._asset_key = key
        self._ws_client = StateClient._get_ws_client()

    @classmethod
    def _get_ws_client(cls):
        """Connect to the simengine ws server
        Returns:
            WebSocket: ws client
        """
        return create_connection(cls.get_connection_str())

    @classmethod
    def _send_request(cls, request, data=None, ws_client=None):
        """Send request to the simengine websocket server
        Args:
            request(ClientToServerRequests): request name
            data(dict): request payload
            ws_client(WebSocket): web socket / client,
                                  this method initializes one if not provided
        """
        if not ws_client:
            ws_client = StateClient._get_ws_client()

        ws_client.send(json.dumps({"request": request.name, "payload": data}))

    @classmethod
    def get_connection_str(cls):
        """Return formatted socket URL for connection"""
        return "ws://{host}:{port}/{path}".format(**StateClient.socket_conf)

    def power_up(self):
        """Send power up request to ws-simengine"""
        StateClient._send_request(
            ClientToServerRequests.set_power,
            {"status": 1, "key": self._asset_key},
            self._ws_client,
        )

    def _state_off(self, hard=False):
        """Send power off request to ws-simengine
        Args:
            hard(bool): flag for abrupt poweroff
        """
        StateClient._send_request(
            ClientToServerRequests.set_power,
            {"status": 0, "key": self._asset_key, "hard": hard},
            self._ws_client,
        )

    def shut_down(self):
        """Graceful shutdown"""
        self._state_off()

    def power_off(self):
        """Abrupt shut off"""
        self._state_off(hard=True)

    def set_sensor_status(self, sensor_name, sensor_value):
        """Request simengine socket server to update runtime BMC sensor value
        Args:
            sensor_name(str): name of the sensor to be updated
            sensor_value(any): new sensor value
        """
        StateClient._send_request(
            ClientToServerRequests.set_sensor_status,
            {
                "key": self._asset_key,
                "sensor_name": sensor_name,
                "sensor_value": sensor_value,
            },
            self._ws_client,
        )

    def set_cv_replacement(self, controller, cv_props):
        """Request simengine socket server to update cache-vault replacement date
        Args:
            controller(int): controller number cv belongs to
            cv_props(dict): new replacement status of the vault & write-through flag
        Returns:
            bool: status indicating if request was succesfully executed
        """
        StateClient._send_request(
            ClientToServerRequests.set_cv_replacement_status,
            {"key": self._asset_key, "controller": controller, **cv_props},
            self._ws_client,
        )

        return json.loads(self._ws_client.recv())["payload"]["executed"]

    def set_controller_prop(self, controller, ctrl_props):
        """Request simengine socket server to update controller properties
        such as memory counts, alarms
        Args:
            controller(int): controller number to be updated
            ctrl_props(dict): including "alarm", correctable
                              & uncorrectable errors as "mem_c_errors", "mem_uc_errors"
        Returns:
            bool: status indicating if request was succesfully executed
        """
        StateClient._send_request(
            ClientToServerRequests.set_controller_status,
            {"key": self._asset_key, "controller": controller, **ctrl_props},
            self._ws_client,
        )

        return json.loads(self._ws_client.recv())["payload"]["executed"]

    def set_physical_drive_prop(self, controller, drive_id, drive_props):
        """Request simengine socket server to update status of a physical drive 
        Args:
            controller(int): controller physical drive belongs to
            drive_id(int): unique drive id (DID) of drive to be updated
            pd_props(dict): including 'media_error_count', 'other_error_count',
                            'predictive_error_count' or 'state'
        Returns:
            bool: status indicating if request was succesfully executed
        """
        StateClient._send_request(
            ClientToServerRequests.set_physical_drive_status,
            {
                "key": self._asset_key,
                "controller": controller,
                "drive_id": drive_id,
                **drive_props,
            },
            self._ws_client,
        )

        return json.loads(self._ws_client.recv())["payload"]["executed"]

    @classmethod
    def power_outage(cls):
        """Send power outage request to ws-simengine (init blackout)"""
        StateClient._send_request(ClientToServerRequests.set_mains, {"mains": 0})

    @classmethod
    def set_ambient(cls, degrees):
        """Send power outage request to ws-simengine (init blackout)"""
        StateClient._send_request(
            ClientToServerRequests.set_ambient, {"degrees": degrees}
        )

    @classmethod
    def set_voltage(cls, voltage):
        """Send voltage update request to ws-simengine"""
        StateClient._send_request(
            ClientToServerRequests.set_voltage, {"voltage": voltage}
        )

    @classmethod
    def power_restore(cls):
        """Send power restore request to ws-simengine"""
        StateClient._send_request(ClientToServerRequests.set_mains, {"mains": 1})

    @classmethod
    def replay_actions(cls, slc=slice(None, None)):
        """Send replay actions recorded by SimEngine request to ws-simening 
        Args:
            slc(slice): range of actions to be performed, replays all if not provided
        """
        StateClient._send_request(
            ClientToServerRequests.replay_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def clear_actions(cls, slc=slice(None, None)):
        """Request ws-simenigne to remove all/range of actions
        Args:
            slc(slice): range of actions to be deleted, removes all if not provided
        """
        StateClient._send_request(
            ClientToServerRequests.clear_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def list_actions(cls, slc=slice(None, None)):
        """Query SimEngine recorder history
        Args:
            slc(slice): range of actions, returns all if not provided
        Returns:
            list: array of dicts containing action details (name, timestamp)
        """
        ws_client = StateClient._get_ws_client()

        StateClient._send_request(
            ClientToServerRequests.get_actions,
            {"range": {"start": slc.start, "stop": slc.stop}},
            ws_client=ws_client,
        )

        return json.loads(ws_client.recv())["payload"]["actions"]

    @classmethod
    def save_actions(cls, filename: str, slc: slice = slice(None, None)):
        """Request simengine to save actions (serialize them into a file)
        Args:
            filename: .json file that will contain actions
            slc: save only this range of actions. Will save all if not provided
        """
        StateClient._send_request(
            ClientToServerRequests.save_actions,
            {"filename": filename, "range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def load_actions(cls, filename: str, slc: slice = slice(None, None)):
        """Request simengine to dynamically load actions from a filename
        Args:
            filename: .json file containing recorded action history
            slc: load only this range of actions
        """
        StateClient._send_request(
            ClientToServerRequests.load_actions,
            {"filename": filename, "range": {"start": slc.start, "stop": slc.stop}},
        )

    @classmethod
    def set_recorder_status(cls, enabled: bool):
        """Update recorder status
        Args:
            enabled: indicates off/on status
        """
        StateClient._send_request(
            ClientToServerRequests.set_recorder_status, {"enabled": enabled}
        )

    @classmethod
    def get_recorder_status(cls) -> dict:
        """Retrieve recorder status 
        Returns:
            dictionary containg "enabled" & "replaying" recorder indicators
        """
        ws_client = StateClient._get_ws_client()

        StateClient._send_request(
            ClientToServerRequests.get_recorder_status, ws_client=ws_client
        )

        return json.loads(ws_client.recv())["payload"]["status"]

    @classmethod
    def rand_actions(cls, rand_options: dict):
        """Request Sim-Engine to perform random action
        Args:
            rand_options: options for the randomizer such as num of iteration,
                           count or time period, 'seconds', asset filter 'asset_keys'
                           and parameters for pauses in-between
                           actions ('min_nap' and 'nap_time')

        """
        StateClient._send_request(
            ClientToServerRequests.exec_rand_actions, {**rand_options}
        )
