"""Web Socket Server (interface to the enginecore)"""

import json
import itertools
import logging
import threading
import time
import random

from circuits import handler, Component, Event
from circuits.net.events import write
from enginecore.state.api import IStateManager, ISystemEnvironment
from enginecore.model.graph_reference import GraphReference
from enginecore.tools.recorder import RECORDER as recorder
from enginecore.tools.randomizer import Randomizer

from enginecore.state.net.ws_requests import (
    ServerToClientRequests,
    ClientToServerRequests,
)

logger = logging.getLogger(__name__)


class WebSocket(Component):
    """a Web-Socket server that handles interactions between:
    - frontend & enginecore
    - cli client & enginecore (see state_client.py)

    WebSocket also manages action recorder, handles replay requests
    
    WebSocket is added as event tracker to the engine so any completion
    events dispatched by engine are passed to websocket client
    """

    channel = "wsserver"

    def __init__(self):
        super().__init__()
        self._clients = []
        self._data_subscribers = []
        # a tiny util to convert json to slice (slice is not serializable)
        self._slice_from_paylaod = lambda d: slice(
            d["payload"]["range"]["start"], d["payload"]["range"]["stop"]
        )

    def connect(self, sock, host, port):
        """Called upon new client connecting to the ws """

        self._clients.append(sock)
        logger.info("WebSocket Client Connected %s:%s", host, port)

    def _write_data(self, sock, request, data):
        """Send data to the web-server socket client
        Args:
            sock(socket): client socket that will receive data
            request(ServerToClientRequests): request type
            data(dict): payload to be sent to the client
        """

        self.fire(
            write(
                sock,
                json.dumps({"request": request.name, "payload": data}, default=str),
            )
        )

    def _cmd_executed_response(self, sock, executed):
        """Update client on command execution status
        (if the request went through or not)"""
        self._write_data(
            sock, ServerToClientRequests.cmd_executed_status, {"executed": executed}
        )

    @handler(ClientToServerRequests.set_power.name)
    def _handle_power_request(self, details):
        """Power up/down asset"""

        power_up = details["payload"]["status"]
        state_manager = IStateManager.get_state_manager_by_key(
            details["payload"]["key"]
        )

        if power_up:
            state_manager.power_up()
        elif "hard" in details["payload"] and details["payload"]["hard"]:
            state_manager.power_off()
        else:
            state_manager.shut_down()

    @handler(ClientToServerRequests.set_layout.name)
    def _handle_layout_request(self, details):
        """Save assets' positions/coordinates"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.save_layout(
                session, details["payload"]["assets"], stage=details["payload"]["stage"]
            )

    @handler(ClientToServerRequests.set_mains.name)
    def _handle_mains_request(self, details):
        """Wallpower update request"""
        if details["payload"]["mains"] == 0:
            ISystemEnvironment.power_outage()
        else:
            ISystemEnvironment.power_restore()

    @handler(ClientToServerRequests.set_ambient.name)
    def _handle_ambient_request(self, details):
        """"Handle ambient changes request"""
        ISystemEnvironment.set_ambient(details["payload"]["degrees"])

    @handler(ClientToServerRequests.set_voltage.name)
    def _handle_voltage_request(self, details):
        """"Handle voltage update"""
        ISystemEnvironment.set_voltage(details["payload"]["voltage"])

    @handler(ClientToServerRequests.exec_play.name)
    def _handle_play_request(self, details):
        """Playback request"""
        IStateManager.execute_play(details["payload"]["name"])

    @handler(ClientToServerRequests.subscribe.name)
    def _handle_subscribe_request(self, details):
        """Subscribe a web-socket client to system updates
        (e.g. battery or status changes)
        """
        self._data_subscribers.append(details["client"])

    @handler(ClientToServerRequests.get_sys_status.name)
    def _handle_status_request(self, details):
        """Get overall system status/details including hardware assets;
        environment state & play details
        """

        assets = IStateManager.get_system_status(flatten=False)
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            stage_layout = GraphReference.get_stage_layout(session)

            # send system topology and assets' power-interconnections
            self._write_data(
                details["client"],
                ServerToClientRequests.sys_layout,
                {"assets": assets, "stageLayout": stage_layout},
            )

        self._write_data(
            details["client"],
            ServerToClientRequests.ambient_upd,
            {"ambient": ISystemEnvironment.get_ambient(), "rising": False},
        )

        self._write_data(
            details["client"],
            ServerToClientRequests.play_list,
            {"plays": list(itertools.chain(*IStateManager.plays()))},
        )

        self._write_data(
            details["client"],
            ServerToClientRequests.mains_upd,
            {"mains": ISystemEnvironment.mains_status()},
        )

    @handler(ClientToServerRequests.replay_actions.name)
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

    @handler(ClientToServerRequests.clear_actions.name)
    def _handle_purge_actions_request(self, details):
        """Clear recorded actions"""
        recorder.erase_range(self._slice_from_paylaod(details))

    @handler(ClientToServerRequests.get_actions.name)
    def _handle_list_actions_request(self, details):
        """Retrieve recorded acitons and send back to the client"""
        self._write_data(
            details["client"],
            ServerToClientRequests.action_list,
            {"actions": recorder.get_action_details(self._slice_from_paylaod(details))},
        )

    @handler(ClientToServerRequests.save_actions.name)
    def _handle_save_history_reqeust(self, details):
        """Save recorder history to a file"""
        recorder.save_actions(
            action_file=details["payload"]["filename"],
            slc=self._slice_from_paylaod(details),
        )

    @handler(ClientToServerRequests.load_actions.name)
    def _handle_load_history_request(self, details):
        """Populate recorder history from a file"""
        recorder.load_actions(
            action_file=details["payload"]["filename"],
            map_key_to_state=IStateManager.get_state_manager_by_key,
            slc=self._slice_from_paylaod(details),
        )

    @handler(ClientToServerRequests.set_recorder_status.name)
    def _handle_set_rec_request(self, details):
        """Disable/Enable recorder status"""
        recorder.enabled = details["payload"]["enabled"]

    @handler(ClientToServerRequests.get_recorder_status.name)
    def _handle_get_rec_request(self, details):
        """Send recorder status to the client"""
        self._write_data(
            details["client"],
            ServerToClientRequests.recorder_status,
            {"status": {"replaying": recorder.replaying, "enabled": recorder.enabled}},
        )

    @handler(ClientToServerRequests.set_sensor_status.name)
    def _handle_sensor_state_request(self, details):
        """Update runtime value of a IPMI/BMC sensor"""
        server_sm = IStateManager.get_state_manager_by_key(details["payload"]["key"])

        server_sm.update_sensor(
            details["payload"]["sensor_name"], details["payload"]["sensor_value"]
        )

    @handler(ClientToServerRequests.set_cv_replacement_status.name)
    def _handle_cv_repl_request(self, details):
        """Update cv details upon a request"""

        payload = details["payload"]
        executed = IStateManager.get_state_manager_by_key(
            payload["key"]
        ).set_cv_replacement(
            payload["controller"],
            payload["replacement_required"],
            payload["write_through_fail"],
        )

        self._cmd_executed_response(details["client"], executed)

    @handler(ClientToServerRequests.set_controller_status.name)
    def _handle_ctrl_update_request(self, details):
        """Update RAID controller when requested"""

        payload = details["payload"]
        executed = IStateManager.get_state_manager_by_key(
            payload["key"]
        ).set_controller_prop(payload["controller"], payload)

        self._cmd_executed_response(details["client"], executed)

    @handler(ClientToServerRequests.set_physical_drive_status.name)
    def _handle_pd_update_request(self, details):
        """Update data related to physical drives when requested"""
        payload = details["payload"]

        executed = IStateManager.get_state_manager_by_key(
            payload["key"]
        ).set_physical_drive_prop(payload["controller"], payload["drive_id"], payload)

        self._cmd_executed_response(details["client"], executed)

    @handler(ClientToServerRequests.exec_rand_actions.name)
    def _handle_rand_act(self, details):
        """Handle perform random actions request"""

        rand_session_specs = details["payload"]
        assets = IStateManager.get_system_status(flatten=True)
        nap = None

        # filter out assets if range is provided
        if rand_session_specs["asset_keys"]:
            assets = list(
                filter(lambda x: x in rand_session_specs["asset_keys"], assets)
            )

        if not assets and not 0 in rand_session_specs["asset_keys"]:
            logger.warning("No assets selected for random actions")
            return

        state_managers = list(map(IStateManager.get_state_manager_by_key, assets))

        if (
            not rand_session_specs["asset_keys"]
            or 0 in rand_session_specs["asset_keys"]
        ):
            state_managers.append(ISystemEnvironment())

        if rand_session_specs["nap_time"]:

            def nap_calc():
                nap_time = lambda: rand_session_specs["nap_time"]
                if rand_session_specs["min_nap"]:
                    nap_time = lambda: random.randrange(
                        rand_session_specs["min_nap"], rand_session_specs["nap_time"]
                    )

                time.sleep(nap_time())

            nap = nap_calc

        rand_t = threading.Thread(
            target=Randomizer.randact,
            args=(state_managers,),
            kwargs={
                "num_iter": rand_session_specs["count"],
                "seconds": rand_session_specs["seconds"],
                "nap": nap,
            },
            name="[#] Randomizer",
        )

        rand_t.daemon = True
        rand_t.start()

    def read(self, sock, data):
        """Read client request
        all request data is sent in a format:
            {
                "request": "request_name",
                "payload": {...} #request_data
            }
        """

        client_data = json.loads(data)
        logger.debug(data)
        self.fire(
            Event.create(
                client_data["request"],
                {"client": sock, "payload": client_data["payload"]},
            )
        )

    def disconnect(self, sock):
        """A client has disconnected """
        self._clients.remove(sock)
        if sock in self._data_subscribers:
            self._data_subscribers.remove(sock)

    # == Engine state handlers (passes engine events to websocket client) ==

    # pylint: disable=unused-argument
    @handler("AssetPowerEvent")
    def on_asset_power_change(self, event, *args, **kwargs):
        """Handle engine events by passing updates to 
        server clients"""
        if not event or event.asset is None:
            return

        client_request = ServerToClientRequests.asset_upd
        payload = {"key": event.asset.key}

        if not event.load.unchanged():
            payload["load"] = event.load.new
        if not event.state.unchanged():
            payload["status"] = event.state.new

        self._notify_clients({"request": client_request.name, "payload": payload})

    @handler("MainsPowerEvent")
    def on_mains_change(self, event, *args, **kwargs):
        """Notify frontend of wallpower changes"""
        client_request = ServerToClientRequests.mains_upd
        payload = {"mains": event.mains.new}
        self._notify_clients({"request": client_request.name, "payload": payload})

    @handler("AmbientEvent")
    def on_ambient_change(self, event, *args, **kwargs):
        """Handle ambient event dispatched by engine so that the server
        client(s) are updated"""
        payload = {
            "ambient": event.temperature.new,
            "rising": event.temperature.difference > 0,
        }
        self._notify_clients(
            {"request": ServerToClientRequests.ambient_upd.name, "payload": payload}
        )

    @handler("AssetLoadEvent")
    def on_asset_load_change(self, event, *args, **kwargs):
        """Handle load changes event propagated by the engine by sending update
        to the frontend"""
        if not event:
            return

        if not event.load.unchanged():
            client_request = ServerToClientRequests.asset_upd
            payload = {"key": event.asset.key, "load": event.load.new}

            self._notify_clients({"request": client_request.name, "payload": payload})

    @handler("BatteryEvent")
    def on_battery_change(self, event, *args, **kwargs):
        """Notify frontend of battery udpate"""
        payload = {"key": event.asset.key, "battery": event.battery.new}
        self._notify_clients(
            {"request": ServerToClientRequests.asset_upd.name, "payload": payload}
        )

    # pylint: enable=unused-argument

    def _notify_clients(self, data):
        """This handler is called upon state changes 
        and is meant to notify web-client of any events 
        
        Args:
            data: data to be sent to ws clients 
                  must be in a format: 
                {
                    "request": <ServerToClientRequests.request.name>,
                    "payload": <data>
                }
        """

        for client in self._data_subscribers:
            self.fireEvent(write(client, json.dumps(data)))
