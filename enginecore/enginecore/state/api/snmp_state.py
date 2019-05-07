"""SNMP device provides access snmp state"""
from collections import namedtuple

from enginecore.state.api.state import IStateManager
from enginecore.model.graph_reference import GraphReference
from enginecore.tools.utils import format_as_redis_key


class ISnmpDeviceStateManager(IStateManager):
    """Stores snmp-related interface features such as access to OIDs"""

    ObjectIdentity = namedtuple("ObjectIdentity", "oid specs")

    def _update_oid_by_name(self, oid_name, value, use_spec=False):
        """Update a specific oid
        Args:
            oid_name(str): oid name defined in device preset file
            value(str): oid value or spec parameter if use_spec is set to True
            use_spec: for enumeration oid types
        Returns:
            bool: true if oid was successfully updated
        """

        with self._graph_ref.get_session() as db_s:
            oid = ISnmpDeviceStateManager.ObjectIdentity(
                *GraphReference.get_asset_oid_by_name(
                    db_s, int(self._asset_key), oid_name
                )
            )

        if oid:
            new_oid_value = oid.specs[value] if use_spec and oid.specs else value
            self._update_oid_value(oid, new_oid_value)
            return True

        return False

    def _update_oid_value(self, object_id, oid_value):
        """Update oid with a new value
        
        Args:
            object_id(ISnmpDeviceStateManager.ObjectIdentity): SNMP object id
            oid_value(object): OID value in rfc1902 format 
        """
        redis_store = IStateManager.get_store()
        rkey = format_as_redis_key(
            str(self._asset_key), object_id.oid, key_formatted=False
        )

        data_type = int(redis_store.get(rkey).decode().split("|")[0])
        rvalue = "{}|{}".format(data_type, oid_value)

        redis_store.set(rkey, rvalue)

    def _get_oid_value(self, object_id, key=None):
        """Retrieve value for a specific OID """
        if key is None:
            key = self.key

        redis_store = IStateManager.get_store()
        rkey = format_as_redis_key(str(key), object_id.oid, key_formatted=False)
        return redis_store.get(rkey).decode().split("|")[1]

    def _get_oid_by_name(self, oid_name):
        """Get oid by oid name"""

        with self._graph_ref.get_session() as db_s:
            oid = ISnmpDeviceStateManager.ObjectIdentity(
                *GraphReference.get_asset_oid_by_name(
                    db_s, int(self._asset_key), oid_name
                )
            )
        return oid
