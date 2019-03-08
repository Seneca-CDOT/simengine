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
  
    def init(self):
        """Initialize socket clients"""
        self._clients = []
    

    def connect(self, sock, host, port):
        """Called upon new client connecting to the ws """

        self._clients.append(sock)
        print("WebSocket Client Connected:", host, port)
        
        # Return assets and their states to the new client
        assets = IStateManager.get_system_status(flatten=False)
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            stage_layout = GraphReference.get_stage_layout(session)

            self._write_data(sock, ClientRequests.topology, {
                'assets': assets, 
                'stageLayout': stage_layout 
            })

        self._write_data(sock, ClientRequests.ambient, {
            'ambient': IStateManager.get_ambient(),
            'rising': False
        })

        self._write_data(sock, ClientRequests.plays, {
            'plays': list(itertools.chain(*IStateManager.plays()))
        })

        self._write_data(sock, ClientRequests.mains, {'mains': IStateManager.mains_status()})


    def _write_data(self, sock, request, data):
        """Send response to the socket client"""

        self.fire(write(sock, json.dumps({
            'request': request.name,
            'data': data
        })))


    def _handle_bad_request(self, request):
        """Handle bad request"""
        logging.error("Bad request !")
        logging.error(request)
        def process_payload(payload):
            logging.error(payload)
        return process_payload


    def _handle_power_request(self, payload):
        """Power up/down asset"""

        power_up = payload['status']
        state_manager = IStateManager.get_state_manager_by_key(payload['key'], SUPPORTED_ASSETS)

        if power_up:
            state_manager.power_up()
        else:
            state_manager.shut_down()


    def _handle_layout_request(self, payload):
        """Save assets' positions/coordinates"""
        with GraphReference().get_session() as session:
            GraphReference.save_layout(session, payload['assets'], stage=payload['stage'])


    def _handle_mains_request(self, payload):
        """Wallpower update request"""
        if payload['mains'] == 0:
            IStateManager.power_outage()
        else:
            IStateManager.power_restore()


    def _handle_play_request(self, payload):
        """Playback request"""
        IStateManager.execute_play(payload['name'])


    def read(self, _, data):
        """Read client request
        all requests are sent in a format:
            {
                "request": "request_name",
                "payload": "request_data"
            }
        """

        client_data = json.loads(data)

        {
            'power': self._handle_power_request,
            'layout': self._handle_layout_request,
            'mains': self._handle_mains_request,
            'play': self._handle_play_request
        }.get(
            client_data['request'],
            lambda: self._handle_bad_request(client_data['request'])
        )(client_data['payload'])


    def disconnect(self, sock):
        """A client has disconnected """
        self._clients.remove(sock)


    @handler('NotifyClient')
    def notify_client(self, data):
        """This handler is called upon state changes & is meant to notify web-client of any events 
        
        Args:
            data: data to be sent to ws clients
        """
        for client in self._clients:
            self.fireEvent(write(client, json.dumps(data)))
            