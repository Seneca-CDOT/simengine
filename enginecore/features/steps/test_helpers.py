"""A collection of shared utils for BDD tests"""
from pysnmp import hlapi
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
