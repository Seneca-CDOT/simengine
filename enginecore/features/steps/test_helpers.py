"""A collection of shared utils for BDD tests"""
import json


from pysnmp import hlapi
import websocket
from circuits import Component


def query_snmp_interface(oid, host="localhost", port=1024):
    """Helper function to query snmp interface of a device"""
    error_indicator, error_status, error_idx, var_binds = next(
        hlapi.getCmd(
            hlapi.SnmpEngine(),
            hlapi.CommunityData("private", mpModel=0),
            hlapi.UdpTransportTarget((host, port)),
            hlapi.ContextData(),
            hlapi.ObjectType(hlapi.ObjectIdentity(oid)),
            lookupMib=False,
        )
    )

    if error_indicator:
        print(error_indicator)
    elif error_status:
        print(
            "%s at %s"
            % (
                error_status.prettyPrint(),
                error_idx and var_binds[int(error_idx) - 1][0] or "?",
            )
        )
    else:
        v_bind = var_binds[0]
        return v_bind[1]

    return None


class FakeEngine(Component):
    """Component facilitating testing"""

    def __init__(self, asset):
        super(FakeEngine, self).__init__()
        self._q_events = None
        asset.register(self)
        self._asset = asset

    def VoltageDecreased_complete(self, evt, e_result):
        """Called on event completion"""
        self.stop()

    def VoltageIncreased_complete(self, evt, e_result):
        """Called on event completion"""
        self.stop()

    def queue_event(self, event):
        """Add event to be fired"""
        self._q_events = event

    def started(self, _):
        """Triggered on run/start"""
        self.fire(self._q_events, self._asset)


class TestClient:
    """WebSocket client for simengine"""

    context = None
    event = None
    queue = None
    web_socket = None

    def __init__(self, url="ws://0.0.0.0:8000/simengine"):
        """Createa a new webs socket client"""
        self._url = url
        self.web_socket = None

    @staticmethod
    def on_message(_, message):
        """Called when simengine sends a new message"""
        parsed_msg = json.loads(message)
        if TestClient.queue:
            TestClient.queue.put(parsed_msg)

    @staticmethod
    def on_open(web_socket):
        """Called when a connection with simengine server is opened"""
        web_socket.send(json.dumps({"request": "subscribe", "payload": {}}))
        TestClient.context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)

    @staticmethod
    def on_error(_, error):
        """Error with a websocket connection"""
        print(error)

    @staticmethod
    def on_close(_):
        """When connection is closed"""
        print("### webscocket client closed ###")

    def run_client(self):
        """run a websocket client"""
        self.web_socket = websocket.WebSocketApp(
            self._url,
            on_message=TestClient.on_message,
            on_error=TestClient.on_error,
            on_close=TestClient.on_close,
        )
        self.web_socket.on_open = TestClient.on_open
        self.web_socket.run_forever()
