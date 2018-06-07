
import json
from circuits import handler, Component
from circuits.net.events import write
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.graph_reference import GraphReference
from enginecore.state.state_managers import StateManger
from pprint import pprint as pp

class WebSocket(Component):

    channel = "wsserver"
  
    def init(self):
        self._clients = []
    
    def connect(self, sock, host, port):
        self._clients.append(sock)
        print("WebSocket Client Connected:", host, port)
        assets = StateManger.get_system_status()
        self.fire(write(sock, json.dumps(assets)))


    def read(self, sock, data):
        self._sock = sock

        data = json.loads(data)
        asset_key = data['key']
        power_up = data['data']['status']
        asset_type = data['data']['type']    
    
        state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_key)
        if power_up:
            state_manager.power_up()
        else:
            state_manager.power_down()

    def disconnect(self, sock):
        print('DISCONNECTING')
        self._clients.remove(sock)

    @handler('notifyClient')
    def notifyClient(self, d):
        self.fireEvent(write(self._clients[0], json.dumps(d))) # TODO: many clients

    