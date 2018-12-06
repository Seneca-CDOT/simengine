""" Web-App Interface """

import json
from enum import Enum

from circuits import handler, Component
from circuits.net.events import write
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.state_managers import StateManager
from enginecore.model.graph_reference import GraphReference


class ClientRequests(Enum):
    """Requests to the client """
    asset = 1
    ambient = 2
    topology = 3
    mains = 4


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
        assets = StateManager.get_system_status(flatten=False)
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            
            stage_layout = GraphReference.get_stage_layout(session)
            # self.fire(write(sock, json.dumps({'assets': assets, 'stageLayout': stage_layout}))) 
            self.fire(write(sock, json.dumps({ 
                'request': ClientRequests.topology.name, 
                'data': {
                    'assets': assets, 
                    'stageLayout': stage_layout 
                }
            }))) 

        self.fire(write(sock, json.dumps({ 
            'request': ClientRequests.ambient.name, 
            'data': {
                'ambient': StateManager.get_ambient(), 
                'rising': False 
            }
        })))

        self.fire(write(sock, json.dumps({ 
            'request': ClientRequests.mains.name, 
            'data': {
                'mains': StateManager.mains_status()
            }
        })))


    def read(self, _, data):
        """Client has sent some request """

        data = json.loads(data)

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            if data['request'] == 'power':
                asset_key = data['key']
                power_up = data['data']['status']
                asset_type = data['data']['type']
                            
                asset_info = GraphReference.get_asset_and_components(session, asset_key)
                state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_info, notify=True)
                
                if power_up:
                    state_manager.power_up()
                else:
                    state_manager.shut_down()
            elif data['request'] == 'layout':
                GraphReference.save_layout(session, data['data']['assets'], stage=data['data']['stage'])
            elif data['request'] == 'mains':
                if data['mains'] == 0:
                    StateManager.power_outage()
                else:
                    StateManager.power_restore()


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
            