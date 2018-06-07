
"""Simple TCP Echo Server
This example shows how you can create a simple TCP Server (an Echo Service)
utilizing the builtin Socket Components that the circuits library ships with.
"""
from circuits import Debugger, handler
from circuits.net.sockets import TCPServer
import json

#!/usr/bin/env python
from circuits import Component, Debugger
from circuits.net.events import write
from circuits.web import Controller, Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher


class WebSocket(Component):

    channel = "wsserver"
  
    def init(self):
        self._clients = []
    
    def connect(self, sock, host, port):
        self._clients.append(sock)
        print("WebSocket Client Connected:", host, port)
        # self.fire(write(sock, "Welcome {0:s}:{1:d}".format(host, port)))

    def read(self, sock, data):
        self._sock = sock
        self.fireEvent(write(sock, "Received: " + data))

    def disconnect(self, sock):
        print('DISCONNECTING')
        self._clients.remove(sock)

    @handler('notifyClient')
    def notifyClient(self, d):
        print('notifyClient  - Echo')
        print(d)
        print(self._clients)
        self.fireEvent(write(self._clients[0], json.dumps(d)))

    