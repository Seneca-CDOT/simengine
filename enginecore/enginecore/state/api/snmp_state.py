"""SNMP device provides access to snmp state including
OIDs & network configurations for snmp"""
from collections import namedtuple
import subprocess

from enginecore.state.api.state import IStateManager
from enginecore.model.graph_reference import GraphReference
from enginecore.tools.utils import format_as_redis_key
from enginecore.state.state_initializer import get_temp_workplace_dir
from enginecore.tools.randomizer import Randomizer


class ISnmpDeviceStateManager(IStateManager):
    """Stores snmp-related interface features such as access to OIDs"""

    ObjectIdentity = namedtuple("ObjectIdentity", "oid specs")

    @property
    def snmp_config(self):
        """Snmp lan configurations"""
        a_info = self._asset_info
        snmp_dir = (
            a_info["workDir"] if "workDir" in a_info else get_temp_workplace_dir()
        )

        return {"host": a_info["host"], "port": a_info["port"], "work_dir": snmp_dir}

    def _execute_ifconfig_cmd(self, command):
        """Execute ifconfig command with ifconfig
        Args:
            command(str): command to be executed """

        subprocess.Popen(
            "ifconfig {}".format(command),
            stderr=subprocess.DEVNULL,
            shell=True,
            close_fds=True,
        )

    def _has_interface(self):
        return "interface" in self._asset_info and self._asset_info["interface"]

    def disable_net_interface(self):
        """Deactivate a network interface attached to this SNMP
        device (if provided with model options)"""
        if not self._has_interface():
            return

        self._execute_ifconfig_cmd("{interface} down".format(**self._asset_info))

    def enable_net_interface(self):
        """Activate a network interface attached to this SNMP
        device (if provided with model options)"""
        if not self._has_interface():
            return

        self._execute_ifconfig_cmd("{interface} {host}".format(**self._asset_info))

        if "mask" in self._asset_info:
            self._execute_ifconfig_cmd(
                "{interface} netmask {mask}".format(**self._asset_info)
            )

    @Randomizer.randomize_method()
    def power_off(self):
        powered = super().power_off()
        if not powered:
            self.disable_net_interface()
        return powered

    @Randomizer.randomize_method()
    def shut_down(self):
        powered = super().shut_down()
        if not powered:
            self.disable_net_interface()
        return powered

    @Randomizer.randomize_method()
    def power_up(self):
        powered = super().power_up()
        if powered:
            self.enable_net_interface()
        return powered

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

    def get_oid_value(self, object_id, key=None):
        """Retrieve value for a specific OID """
        if key is None:
            key = self.key

        redis_store = IStateManager.get_store()
        rkey = format_as_redis_key(str(key), object_id.oid, key_formatted=False)
        return redis_store.get(rkey).decode().split("|")[1]

    def get_oid_by_name(self, oid_name):
        """Get oid by oid name"""

        with self._graph_ref.get_session() as db_s:
            oid = ISnmpDeviceStateManager.ObjectIdentity(
                *GraphReference.get_asset_oid_by_name(
                    db_s, int(self._asset_key), oid_name
                )
            )
        return oid
