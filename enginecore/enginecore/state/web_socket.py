""" Web-App Interface """

import json
from circuits import handler, Component
from circuits.net.events import write
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.state_managers import StateManger
from enginecore.model.graph_reference import GraphReference

class WebSocket(Component):
    """Simple Web-Socket server that handles interactions between frontend & enginecore """

    channel = "wsserver"
  
    def init(self):
        """ Initialize socket clients"""
        self._clients = []
    

    def connect(self, sock, host, port):
        """ Called upon new client connecting to the ws """

        self._clients.append(sock)
        print("WebSocket Client Connected:", host, port)
        
        # Return assets and their states to the new client
        assets = StateManger.get_system_status(flatten=False)
        self.fire(write(sock, json.dumps(assets)))


    def read(self, _, data):
        """ Client has sent some request """

        data = json.loads(data)
        asset_key = data['key']
        power_up = data['data']['status']
        asset_type = data['data']['type']

        with GraphReference().get_session() as session:
            
            asset_info = GraphReference.get_asset_and_components(session, asset_key)
            state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_info, notify=True)
            
            if power_up:
                state_manager.power_up()
            else:
                state_manager.shut_down()


    def disconnect(self, sock):
        """ A client has disconnected """
        self._clients.remove(sock)


    @handler('NotifyClient')
    def notify_client(self, data):
        """ This handler is called upon state changes & is meant to notify web-client of any events 
        
        Args:
            data: data to be sent to clients
        """
        for client in self._clients:
            self.fireEvent(write(client, json.dumps(data)))
            