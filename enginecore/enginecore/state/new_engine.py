import logging
import os
import math
import functools
import queue
import threading

from circuits import Component, Event, Worker, Debugger  # , task
from circuits import Event

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.hardware.event_results import (
    PowerEventResult,
    LoadEventResult,
    VoltageEventResult,
)

from enginecore.state.hardware.room import ServerRoom, Asset

from enginecore.tools.recorder import RECORDER
from enginecore.state.api import ISystemEnvironment
from enginecore.state.event_map import PowerEventMap
from enginecore.state.net.ws_server import WebSocket
from enginecore.state.net.ws_requests import ServerToClientRequests

from enginecore.model.graph_reference import GraphReference
from enginecore.state.state_initializer import initialize, clear_temp


class VoltageEvent(Event):
    pass


class ParentVoltageUpEvent(Event):
    pass


class ParentVoltageDownEvent(Event):
    pass


class ChildLoadUpEvent(Event):
    pass


class ChildLoadDownEvent(Event):
    pass


class EventBatch:
    def __init__(self, keys, event):
        self._keys = keys
        self._event = event


class PowerIteration:

    data_source = None

    def __init__(self, src_event):
        """Source """
        self._src_event = src_event
        self._graph_ref = GraphReference()

    def launch(self):
        """Start up power iteration by returning events
        Returns:
            tuple consisting of:
                - ParentVoltageEvent (either up or down)
                - ChildLoadEvent     (either up or down)
        """

        # asset caused power loop
        if self._src_event.kwargs["asset"]:
            return self._process_hardware_asset_event()

        # wallpower voltage caused power loop
        else:
            return self._process_wallpower_event(), None

    def _map_volt_event(self):
        if (
            self._src_event.kwargs["old_out_volt"]
            > self._src_event.kwargs["new_out_volt"]
            or self._src_event.kwargs["new_out_volt"] == 0
        ):
            volt_event = ParentVoltageDownEvent
        else:
            volt_event = ParentVoltageUpEvent

        return volt_event

    def _process_wallpower_event(self):
        wall_power_out_keys = self.data_source.get_mains_powered_assets()

        return (
            wall_power_out_keys,
            functools.partial(
                self._map_volt_event(),
                old_in_volt=self._src_event.kwargs["old_out_volt"],
                new_in_volt=self._src_event.kwargs["new_out_volt"],
            ),
        )

    def _process_hardware_asset_event(self):
        child_keys, parent_keys = self.data_source.get_affected_assets(
            self._src_event.kwargs["asset"].key
        )
        # load_change = (1 if new_state else -1) * updated_asset.state.power_usage

        return (
            (
                child_keys,
                functools.partial(
                    self._map_volt_event(),
                    old_in_volt=self._src_event.kwargs["old_out_volt"],
                    new_in_volt=self._src_event.kwargs["new_out_volt"],
                ),
            ),
            None,
        )


class HardwareDataSource:
    graph_ref = GraphReference()

    @classmethod
    def get_all_assets(cls):
        return NotImplementedError()

    @classmethod
    def get_affected_assets(cls, asset_key):
        return NotImplementedError()

    @classmethod
    def get_mains_powered_assets(cls):
        return NotImplementedError()


class HardwareGraphDataSource(HardwareDataSource):
    graph_ref = GraphReference()

    @classmethod
    def get_all_assets(cls):
        with cls.graph_ref.get_session() as session:
            return GraphReference.get_assets_and_children(session)

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_affected_assets(cls, asset_key):
        with cls.graph_ref.get_session() as session:
            childen, parents, _ = GraphReference.get_affected_assets(session, asset_key)

        return ([a["key"] for a in childen], [a["key"] for a in parents])

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_mains_powered_assets(cls):
        with cls.graph_ref.get_session() as session:
            return GraphReference.get_mains_powered_outlets(session)


class Engine(Component):
    """Top-level component that instantiates assets"""

    def __init__(self, force_snmp_init=True, data_source=HardwareGraphDataSource):
        super(Engine, self).__init__()

        ### Set-up WebSocket & Redis listener ###
        logging.info("Starting simengine daemon...")

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}

        self._sys_environ = ServerRoom().register(self)
        self._power_iter_queue = queue.Queue()
        self._worker_thread = None
        self._data_source = data_source
        PowerIteration.data_source = data_source

        # Register assets and reset power state
        self._reload_model(force_snmp_init)
        logging.info("Physical Environment:\n%s", self._sys_environ)

    def _reload_model(self, force_snmp_init=True):
        """Re-create system topology (instantiate assets based on graph ref)"""

        RECORDER.enabled = False
        logging.info("Initializing system topology...")

        self._assets = {}

        # init state
        clear_temp()
        initialize(force_snmp_init)

        # get system topology
        assets = self._data_source.get_all_assets()

        for asset in assets:
            self._assets[asset["key"]] = Asset.get_supported_assets()[asset["type"]](
                asset
            ).register(self)

        ISystemEnvironment.set_ambient(21)
        RECORDER.enabled = True

        # initialize power processing thread
        self._worker_thread = threading.Thread(
            target=self.power_worker, name="power_worker"
        )
        self._worker_thread.daemon = True

        self._worker_thread.start()

    def power_worker(self):
        while True:
            # new power-loop was initialized
            next_power_iter = self._power_iter_queue.get()
            print("New power iteration")
            volt_events, load_events = next_power_iter.launch()

            for asset_key in volt_events[0]:
                self.fire(volt_events[1](), self._assets[asset_key])

            self._power_iter_queue.task_done()

    def handle_ambient_update(self, old_temp, new_temp):
        """Ambient changes to a new value, initiate a chain of thermal reactions
        Args:
            old_temp(float): old room temperature
            new_temp(float): new room temperature
        """
        pass

    def handle_voltage_update(self, old_voltage, new_voltage):
        """Wallpower voltage changes to a new value,
        initiate a chain of power reactions
        Args:
            old_voltage(float): old voltage value
            new_voltage(float): new wallpower voltage value
        """

        volt_event = VoltageEvent(
            asset=None, old_out_volt=old_voltage, new_out_volt=new_voltage
        )

        self._power_iter_queue.put(PowerIteration(volt_event))

    def handle_state_update(self, asset_key, state):
        """Asset state changes to a new value,
        initiate a chain of power reactions
        Args:
            asset_key(int): key of the updated asset
            state(int): 0 for offline, 1 for online
        """

        out_volt = self._assets[asset_key].state.output_voltage

        volt_event = VoltageEvent(
            asset=self._assets[asset_key],
            old_out_volt=(state ^ 1) * out_volt,
            new_out_volt=state * out_volt,
        )

        self._power_iter_queue.put(PowerIteration(volt_event))

    def handle_oid_update(self, asset_key, oid, value):
        pass
