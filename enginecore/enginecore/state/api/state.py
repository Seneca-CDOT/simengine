"""Interface for asset state management"""

import time
from enum import Enum
from functools import lru_cache
import os
import subprocess
import json

import redis

from enginecore.model.graph_reference import GraphReference
from enginecore.state.redis_channels import RedisChannels

from enginecore.tools.recorder import RECORDER as record
from enginecore.tools.randomizer import Randomizer
from enginecore.state.api.environment import ISystemEnvironment


@Randomizer.register
class IStateManager:
    """Base class for all the state managers """

    redis_store = None

    class PowerStateReason(Enum):
        """Describes reason behind asset power state"""

        ac_restored = 1
        ac_lost = 2
        turned_on = 3
        turned_off = 4
        signal_on = 5
        signal_off = 6

    def __init__(self, asset_info):
        self._graph_ref = GraphReference()
        self._asset_key = asset_info["key"]
        self._asset_info = asset_info

    def close_connection(self):
        """Close bolt driver connections"""
        self._graph_ref.close()

    @property
    def key(self) -> int:
        """Asset Key """
        return self._asset_key

    @property
    def redis_key(self) -> str:
        """Asset key in redis format as '{key}-{type}' """
        return "{}-{}".format(str(self.key), self.asset_type)

    @property
    def asset_type(self) -> str:
        """Asset Type """
        return self._asset_info["type"]

    @property
    def power_on_ac_restored(self) -> bool:
        """Returns true if asset is configured to power up when AC
        is restored (voltage is above lower threshold)"""
        return (
            self._asset_info["powerOnAc"] if "powerOnAc" in self._asset_info else True
        )

    @property
    def power_usage(self):
        """Normal power usage in AMPS when powered up"""
        if self.input_voltage and "powerConsumption" in self._asset_info:
            return self._asset_info["powerConsumption"] / self.input_voltage

        return 0.0

    @property
    def draw_percentage(self) -> float:
        """How much power the asset draws"""
        return self._asset_info["draw"] if "draw" in self._asset_info else 1

    @property
    def power_consumption(self):
        """How much power this device consumes (wattage)"""
        return (
            self._asset_info["powerConsumption"]
            if "powerConsumption" in self._asset_info
            else 0
        )

    @property
    def asset_info(self) -> dict:
        """Get information associated with the asset"""
        return self._asset_info

    @property
    def load(self):
        """Get current load stored in redis (in AMPs)"""
        return float(IStateManager.get_store().get(self.redis_key + ":load"))

    @property
    def wattage(self):
        """Asset wattage (assumes power-source to be 120v)"""
        return self.load * self.input_voltage

    def min_voltage_prop(self):
        """Get minimum voltage required and the poweroff timeout associated with it"""

        if not "minVoltage" in self._asset_info:
            return 0

        return self._asset_info["minVoltage"]

    @property
    def status(self):
        """Operational State 
        
        Returns:
            int: 1 if on, 0 if off
        """
        return int(IStateManager.get_store().get(self.redis_key + ":state"))

    @property
    def input_voltage(self):
        """Asset input voltage in Volts"""
        in_volt = IStateManager.get_store().get(self.redis_key + ":in-voltage")
        return float(in_volt) if in_volt else 0.0

    @property
    def output_voltage(self):
        """Output voltage for the device"""
        return self.input_voltage * self.status

    @property
    def agent(self):
        """Agent instance details (if supported)
        
        Returns:
            tuple: process id and status of the process (if it's running)
        """
        pid = IStateManager.get_store().get(self.redis_key + ":agent")
        return (
            (int(pid), os.path.exists("/proc/" + pid.decode("utf-8"))) if pid else None
        )

    @record
    @Randomizer.randomize_method()
    def shut_down(self):
        """Implements state logic for graceful power-off event,
        sleeps for the pre-configured time
            
        Returns:
            int: Asset's status after power-off operation
        """
        if self.status:
            self._sleep_shutdown()
            self._set_state_off()
            return 0
        return self.status

    @record
    @Randomizer.randomize_method()
    def power_off(self):
        """Implements state logic for abrupt power loss 
        
        Returns:
            int: Asset's status after power-off operation
        """
        if self.status:
            self._set_state_off()
            return 0
        return self.status

    @record
    @Randomizer.randomize_method()
    def power_up(self):
        """Implements state logic for power up;
        sleeps for the pre-configured time & resets boot time
        
        Returns:
            int: Asset's status after power-on operation
        """
        if self._parents_available() and not self.status:
            self._sleep_powerup()
            # update machine start time & turn on
            self._reset_boot_time()
            self._set_state_on()
            return 1
        return self.status

    def _update_input_voltage(self, voltage: float):
        """Set input voltage"""
        voltage = max(voltage, 0)
        IStateManager.get_store().set(self.redis_key + ":in-voltage", voltage)

    def _update_load(self, load: float):
        """Update power load for the asset"""
        load = max(load, 0.0)
        IStateManager.get_store().set(self.redis_key + ":load", load)

    def _sleep_delay(self, delay_type):
        """Sleep for n number of ms determined by the delay_type"""
        if delay_type in self._asset_info:
            time.sleep(self._asset_info[delay_type] / 1000.0)  # ms to sec

    def _sleep_shutdown(self):
        """Hardware-specific shutdown delay"""
        self._sleep_delay("offDelay")

    def _sleep_powerup(self):
        """Hardware-specific powerup delay"""
        self._sleep_delay("onDelay")

    def _set_redis_asset_state(self, state):
        """Update redis value of the asset power status"""
        IStateManager.get_store().set(self.redis_key + ":state", state)

    def _set_state_on(self):
        """Set state to online"""
        self._publish_power(self.status, 1)

    def _set_state_off(self):
        """Set state to offline"""
        self._publish_power(self.status, 0)

    def _publish_power(self, old_state, new_state):
        """Notify daemon of power updates"""
        IStateManager.get_store().publish(
            RedisChannels.state_update_channel,
            json.dumps(
                {"key": self.key, "old_state": old_state, "new_state": new_state}
            ),
        )

    def _reset_boot_time(self):
        """Reset device start time (this redis key/value is used to calculate uptime)
        (see snmppub.lua)
        """
        IStateManager.get_store().set(
            str(self._asset_key) + ":start_time", int(time.time())
        )

    def _check_parents(
        self, keys, parent_down, msg="Cannot perform the action: [{}] parent is off"
    ):
        """Check that redis values pass certain condition
        
        Args:
            keys (list): Redis keys (formatted as required)
            parent_down (callable): lambda clause 
            msg (str, optional): Error message to be printed
        
        Returns: 
            bool: True if parent keys are missing or all parents 
                  were verified with parent_down clause 
        """
        if not keys:
            return True

        parent_values = IStateManager.get_store().mget(keys)
        pdown_msg = []

        for rkey, rvalue in zip(keys, parent_values):
            if parent_down(rvalue, rkey):
                pdown_msg.append(msg.format(rkey))

        if len(pdown_msg) == len(keys):
            print("\n".join(pdown_msg))
            return False

        return True

    def _parents_available(self):
        """Indicates whether a state action can be performed;
        checks if parent nodes are up & running and all OIDs indicate 'on' status
        
        Returns:
            bool: True if parents are available
        """

        asset_keys, oid_keys = GraphReference.get_parent_keys(
            self._graph_ref.get_session(), self._asset_key
        )

        # if wall-powered, check the mains
        if not asset_keys and not ISystemEnvironment.power_source_available():
            return False

        state_managers = list(map(self.get_state_manager_by_key, asset_keys))
        min_volt_value = self.min_voltage_prop()

        # check if power is present
        enough_voltage = len(
            list(filter(lambda sm: sm.output_voltage > min_volt_value, state_managers))
        )
        parent_assets_up = len(list(filter(lambda sm: sm.status, state_managers)))

        oid_clause = (
            lambda rvalue, rkey: rvalue.split(b"|")[1].decode()
            == oid_keys[rkey]["switchOff"]
        )
        oids_on = self._check_parents(oid_keys.keys(), oid_clause)

        return (parent_assets_up and enough_voltage and oids_on) or (not asset_keys)

    def __str__(self):
        return (
            "Asset[{0.asset_type}][{0.key}] \n"
            " - Status: {0.status} \n"
            " - Load: {0.load}A\n"
            " - Power Consumption: {0.power_consumption}W \n"
            " - Input Voltage: {0.input_voltage}V\n"
            " - Output Voltage: {0.output_voltage}V\n"
        ).format(self)

    @classmethod
    def get_store(cls):
        """Get redis db handler """
        if not cls.redis_store:
            cls.redis_store = redis.StrictRedis(host="localhost", port=6379)

        return cls.redis_store

    @classmethod
    def _get_assets_states(cls, assets, flatten=True):
        """Query redis store and find states for each asset

        Args:
            flatten(bool): If false, the returned assets in the dict
                           will have their child-components nested
        Returns:
            dict: Current information on assets including their states, load etc.
        """
        asset_keys = assets.keys()

        if not asset_keys:
            return None

        asset_values = cls.get_store().mget(
            list(map(lambda k: "{}-{}:state".format(k, assets[k]["type"]), asset_keys))
        )

        for rkey, rvalue in zip(assets, asset_values):
            asset_state = cls.get_state_manager_by_key(rkey)

            assets[rkey]["status"] = int(rvalue)
            assets[rkey]["load"] = asset_state.load

            if assets[rkey]["type"] == "ups":
                assets[rkey]["battery"] = asset_state.battery_level

            if not flatten and "children" in assets[rkey]:
                # call recursively on children
                assets[rkey]["children"] = cls._get_assets_states(
                    assets[rkey]["children"]
                )

        return assets

    @classmethod
    def get_system_status(cls, flatten=True):
        """Get states of all system components 
        
        Args:
            flatten(bool): If false, the returned assets in the dict 
                           will have their child-components nested
        
        Returns:
            dict: Current information on assets including their states, load etc.
        """
        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            # cache assets
            assets = GraphReference.get_assets_and_connections(session, flatten)
            return cls._get_assets_states(assets, flatten)

    @classmethod
    @lru_cache(maxsize=32)
    def get_state_manager_by_key(cls, key, supported_assets=None):
        """Infer asset manager from key"""
        from enginecore.state.hardware.room import Asset

        if not supported_assets:
            supported_assets = Asset.get_supported_assets()

        graph_ref = GraphReference()

        with graph_ref.get_session() as session:
            asset_info = GraphReference.get_asset_and_components(session, key)

        sm_mro = supported_assets[asset_info["type"]].StateManagerCls.mro()

        module = ".".join(__name__.split(".")[:-1])  # api module
        return next(filter(lambda x: x.__module__.startswith(module), sm_mro))(
            asset_info
        )

    @classmethod
    def asset_exists(cls, key):
        """Check if asset with the key exists"""
        graph_ref = GraphReference()

        with graph_ref.get_session() as session:
            asset_info = GraphReference.get_asset_and_components(session, key)
            return asset_info is not None

    @classmethod
    def set_play_path(cls, path):
        """Update play folder containing scripts"""

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            GraphReference.set_play_path(session, path)

    @classmethod
    def plays(cls):
        """Get plays (user-defined scripts) available for execution
        Returns:
            tuple: list of bash files as well as python scripts
        """

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:
            play_path = GraphReference.get_play_path(session)

        if not play_path:
            return ([], [])

        play_files = [
            f
            for f in os.listdir(play_path)
            if os.path.isfile(os.path.join(play_path, f))
        ]

        is_py_file = lambda f: os.path.splitext(f)[1] == ".py"

        return (
            [os.path.splitext(f)[0] for f in play_files if not is_py_file(f)],
            [os.path.splitext(f)[0] for f in play_files if is_py_file(f)],
        )

    @classmethod
    def execute_play(cls, play_name):
        """Execute a specific play
        Args:
            play_name(str): playbook name
        """

        graph_ref = GraphReference()
        with graph_ref.get_session() as session:

            play_path = GraphReference.get_play_path(session)
        if not play_path:
            return

        file_filter = (
            lambda f: os.path.isfile(os.path.join(play_path, f))
            and os.path.splitext(f)[0] == play_name
        )

        play_file = [f for f in os.listdir(play_path) if file_filter(f)][0]

        subprocess.Popen(
            os.path.join(play_path, play_file),
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
