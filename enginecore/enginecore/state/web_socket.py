""" Web-App Interface """

import json
from enum import Enum
import itertools
import logging

from circuits import handler, Component
from circuits.net.events import write
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.api import IStateManager
from enginecore.model.graph_reference import GraphReference


class ClientRequests(Enum):
    """Requests to the client """
    asset = 1
    ambient = 2
    topology = 3
    mains = 4
    plays = 5


class WebSocket(Component):
    """Simple Web-Socket server that handles interactions between frontend & enginecore """

    channel = "wsserver"


    def __init__(self):
        super().__init__()
        self._clients = []
        self._data_subscribers = []


    def connect(self, sock, host, port):
        """Called upon new client connecting to the ws """

        self._clients.append(sock)
        logging.info("WebSocket Client Connected %s:%s", host, port)


    def _write_data(self, sock, request, data):
        """Send response to the socket client"""

        self.fire(write(sock, json.dumps({
            'request': request.name,
            'payload': data
        })))


    def _handle_bad_request(self, request):
        """Handle bad request"""

        logging.error("Cannot process '%s' request: ", request)
        def process_payload(details):
            logging.error("Received payload with '%s' request from client '%s':", request, details['client'])
            logging.error(details['payload'])
        return process_payload


    def _handle_power_request(self, details):
        """Power up/down asset"""

        power_up = details['payload']['status']
        state_manager = IStateManager.get_state_manager_by_key(details['payload']['key'], SUPPORTED_ASSETS)

        if power_up:
            state_manager.power_up()
        else:
            state_manager.shut_down()


    def _handle_layout_request(self, details):
        """Save assets' positions/coordinates"""
        with GraphReference().get_session() as session:
            GraphReference.save_layout(session, details['payload']['assets'], stage=details['payload']['stage'])


    def _handle_mains_request(self, details):
        """Wallpower update request"""
        if details['payload']['mains'] == 0:
            IStateManager.power_outage()
        else:
            IStateManager.power_restore()


    def _handle_play_request(self, details):
        """Playback request"""
        IStateManager.execute_play(details['payload']['name'])


    def _handle_subscribe_request(self, details):
        """Subscribe a web-socket client to system updates (e.g. battery or status changes) """
        self._data_subscribers.append(details['client'])


    def _handle_status_request(self, details):
        """Get overall system status/details including hardware assets, environment state & play details"""

        assets = IStateManager.get_system_status(flatten=False)
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            stage_layout = GraphReference.get_stage_layout(session)

            self._write_data(details['client'], ClientRequests.topology, {
                'assets': assets, 
                'stageLayout': stage_layout 
            })

        self._write_data(details['client'], ClientRequests.ambient, {
            'ambient': IStateManager.get_ambient(),
            'rising': False
        })

        self._write_data(details['client'], ClientRequests.plays, {
            'plays': list(itertools.chain(*IStateManager.plays()))
        })

        self._write_data(details['client'], ClientRequests.mains, {'mains': IStateManager.mains_status()})


    def read(self, sock, data):
        """Read client request
        all requests are sent in a format:
            {
                "request": "request_name",
                "payload": "request_data"
            }
        """

        client_data = json.loads(data)
        logging.info(client_data)

        # map request names to functions, report 'bad' request on error
        {
            'power': self._handle_power_request,
            'layout': self._handle_layout_request,
            'mains': self._handle_mains_request,
            'play': self._handle_play_request,
            'status': self._handle_status_request,
            'subscribe': self._handle_subscribe_request,
        }.get(
            client_data['request'],
            # default to bad request
            lambda: self._handle_bad_request(client_data['request'])
        )({
            "client": sock,
            "payload": client_data['payload']
        })


    def disconnect(self, sock):
        """A client has disconnected """
        self._clients.remove(sock)
        if sock in  self._data_subscribers:
            self._data_subscribers.remove(sock)


    @handler('NotifyClient')
    def notify_client(self, data):
        """This handler is called upon state changes & is meant to notify web-client of any events 
        
        Args:
            data: data to be sent to ws clients
        """

        for client in self._data_subscribers:
            self.fireEvent(write(client, json.dumps(data)))
