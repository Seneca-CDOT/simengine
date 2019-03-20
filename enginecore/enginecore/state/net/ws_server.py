"""Web Socket Server (interface to the enginecore)"""

import json
from enum import Enum
import itertools
import logging
import threading

from circuits import handler, Component
from circuits.net.events import write
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.api import IStateManager, IBMCServerStateManager
from enginecore.model.graph_reference import GraphReference
from enginecore.state.recorder import RECORDER as recorder
from enginecore.state.net.ws_requests import (
    ServerToClientRequests,
    ClientToServerRequests,
)


class WebSocket(Component):
    """Simple Web-Socket server that handles interactions between frontend & enginecore """

    channel = "wsserver"

    def __init__(self):
        super().__init__()
        self._clients = []
        self._data_subscribers = []
        self._slice_from_paylaod = lambda d: slice(
            d["payload"]["range"]["start"], d["payload"]["range"]["stop"]
        )

    def connect(self, sock, host, port):
        """Called upon new client connecting to the ws """

        self._clients.append(sock)
        logging.info("WebSocket Client Connected %s:%s", host, port)

    def _write_data(self, sock, request, data):
        """Send response to the socket client"""

        self.fire(
            write(
                sock,
                json.dumps({"request": request.name, "payload": data}, default=str),
            )
        )

    def _handle_bad_request(self, request):
        """Handle bad request"""

        def process_payload(details):
            logging.error("Cannot process '%s' request: ", request)
            logging.error(
                "Received payload with '%s' request from client '%s':",
                request,
                details["client"],
            )
            logging.error(details["payload"])

        return process_payload

    def _handle_power_request(self, details):
        """Power up/down asset"""

        power_up = details["payload"]["status"]
        state_manager = IStateManager.get_state_manager_by_key(
            details["payload"]["key"], SUPPORTED_ASSETS
        )

        if power_up:
            state_manager.power_up()
        elif "hard" in details["payload"] and details["payload"]["hard"]:
            state_manager.power_off()
        else:
            state_manager.shut_down()

    def _handle_layout_request(self, details):
        """Save assets' positions/coordinates"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.save_layout(
                session, details["payload"]["assets"], stage=details["payload"]["stage"]
            )

    def _handle_mains_request(self, details):
        """Wallpower update request"""
        if details["payload"]["mains"] == 0:
            IStateManager.power_outage()
        else:
            IStateManager.power_restore()

    def _handle_play_request(self, details):
        """Playback request"""
        IStateManager.execute_play(details["payload"]["name"])

    def _handle_subscribe_request(self, details):
        """Subscribe a web-socket client to system updates (e.g. battery or status changes) """
        self._data_subscribers.append(details["client"])

    def _handle_status_request(self, details):
        """Get overall system status/details including hardware assets, environment state & play details"""

        assets = IStateManager.get_system_status(flatten=False)
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            stage_layout = GraphReference.get_stage_layout(session)

            self._write_data(
                details["client"],
                ServerToClientRequests.topology,
                {"assets": assets, "stageLayout": stage_layout},
            )

        self._write_data(
            details["client"],
            ServerToClientRequests.ambient,
            {"ambient": IStateManager.get_ambient(), "rising": False},
        )

        self._write_data(
            details["client"],
            ServerToClientRequests.plays,
            {"plays": list(itertools.chain(*IStateManager.plays()))},
        )

        self._write_data(
            details["client"],
            ServerToClientRequests.mains,
            {"mains": IStateManager.mains_status()},
        )

    def _handle_replay_actions_request(self, details):
        """Replay all or range of actions stored by the recorder"""
        recorder.get_action_details()
        replay_t = threading.Thread(
            target=recorder.replay_range,
            kwargs={"slc": self._slice_from_paylaod(details)},
            name="[>] replay",
        )

        replay_t.daemon = True
        replay_t.start()

    def _handle_purge_actions_request(self, details):
        """Clear recorded actions"""
        recorder.erase_range(self._slice_from_paylaod(details))

    def _handle_list_actions_request(self, details):
        """Retrieve recorded acitons and send back to the client"""
        self._write_data(
            details["client"],
            ServerToClientRequests.action_list,
            {"actions": recorder.get_action_details(self._slice_from_paylaod(details))},
        )

    def _handle_set_rec_request(self, details):
        """Disable/Enable recorder status"""
        recorder.enabled = details["payload"]["enabled"]

    def _handle_get_rec_request(self, details):
        """Send recorder status to the client"""
        self._write_data(
            details["client"],
            ServerToClientRequests.recorder_status,
            {"status": {"replaying": recorder.replaying, "enabled": recorder.enabled}},
        )

    def _handle_sensor_state_request(self, details):
        """Update runtime value of a IPMI/BMC sensor"""
        server_sm = IStateManager.get_state_manager_by_key(
            details["payload"]["key"], SUPPORTED_ASSETS
        )

        server_sm.update_sensor(
            details["payload"]["sensor_name"], details["payload"]["sensor_value"]
        )

    def _handle_cv_repl_request(self, detials):

        payload = detials["payload"]
        IBMCServerStateManager.set_cv_replacement(
            payload["key"],
            payload["controller"],
            payload["repl_status"],
            payload["wt_on_fail"],
        )

    def read(self, sock, data):
        """Read client request
        all requests are sent in a format:
            {
                "request": "request_name",
                "payload": {...} #request_data
            }
        """

        client_data = json.loads(data)
        logging.info(client_data)

        # map request names to functions, report 'bad' request on error
        {
            ClientToServerRequests.power: self._handle_power_request,
            ClientToServerRequests.layout: self._handle_layout_request,
            ClientToServerRequests.mains: self._handle_mains_request,
            ClientToServerRequests.play: self._handle_play_request,
            ClientToServerRequests.status: self._handle_status_request,
            ClientToServerRequests.subscribe: self._handle_subscribe_request,
            ClientToServerRequests.replay_actions: self._handle_replay_actions_request,
            ClientToServerRequests.purge_actions: self._handle_purge_actions_request,
            ClientToServerRequests.list_actions: self._handle_list_actions_request,
            ClientToServerRequests.set_recorder_status: self._handle_set_rec_request,
            ClientToServerRequests.get_recorder_status: self._handle_get_rec_request,
            ClientToServerRequests.sensor: self._handle_sensor_state_request,
            ClientToServerRequests.cv_replacement_status: self._handle_cv_repl_request,
        }.get(
            ClientToServerRequests[client_data["request"]],
            # default to bad request
            self._handle_bad_request(client_data["request"]),
        )(
            {"client": sock, "payload": client_data["payload"]}
        )

    def disconnect(self, sock):
        """A client has disconnected """
        self._clients.remove(sock)
        if sock in self._data_subscribers:
            self._data_subscribers.remove(sock)

    @handler("NotifyClient")
    def notify_client(self, data):
        """This handler is called upon state changes & is meant to notify web-client of any events 
        
        Args:
            data: data to be sent to ws clients
        """

        for client in self._data_subscribers:
            self.fireEvent(write(client, json.dumps(data)))
