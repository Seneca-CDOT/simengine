import logging

import queue
import threading
import math

from circuits import Component, Event, Worker, Debugger, handler

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.hardware.room import ServerRoom, Asset

from enginecore.tools.recorder import RECORDER
from enginecore.state.api import ISystemEnvironment
from enginecore.state.net.ws_server import WebSocket
from enginecore.state.net.ws_requests import ServerToClientRequests

from enginecore.state.state_initializer import initialize, clear_temp, configure_env
from enginecore.state.engine_data_source import HardwareGraphDataSource
from enginecore.state.power_iteration import PowerIteration
from enginecore.state.power_events import AssetPowerEvent


class AllVoltageBranchesDone(Event):
    """Dispatched when power iteration finishes downstream
    voltage event propagation to all the leaf nodes that 
    are descendants of the iteration source event"""

    success = True


class AllLoadBranchesDone(Event):
    """Dispatched when power iteration finishes upstream
    load event propagation across all load branches"""

    success = True


class Engine(Component):
    """Top-level component that initializes assets & handles state changes
    (thermal, power, oid) by dispatching events against hardware assets.

    It can propagate the following events:
        - Ambient Changes (AmbientUpEvent/AmbientDownEvent)
        - Input voltage changes either due to wallpower power state update
          or a power-supplying asset going down/up
          (InputVoltageUpEvent/InputVoltageUpEvent)
        - Load updates due to voltage changes
    """

    def __init__(
        self, force_snmp_init=True, debug=True, data_source=HardwareGraphDataSource
    ):
        super(Engine, self).__init__()

        ### Set-up WebSocket & Redis listener ###
        logging.info("Starting simengine daemon...")
        # TODO: when hooked into redis, either remove this or one from redis
        configure_env(debug)

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}

        self._completion_trackers = []

        self._sys_environ = ServerRoom().register(self)
        self._power_iter_queue = queue.Queue()
        self._current_power_iter = None

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
        """Consumer processing power event queue"""

        while True:
            # new power-loop was initialized
            next_power_iter = self._power_iter_queue.get()

            if not next_power_iter:
                return

            assert self._current_power_iter is None

            self._current_power_iter = next_power_iter
            print("--------------------")
            print("New power iteration")
            print("--------------------")

            self._chain_power_events(*self._current_power_iter.launch())

    def _notify_trackers(self, event):
        """Dispatch power completion events to clients"""

        for comp_tracker in self._completion_trackers:
            self.fire(event(), comp_tracker)

    def subscribe_tracker(self, tracker):
        """Subcribe external engine client to completion events"""
        self._completion_trackers.append(tracker.register(self))

    def unsubscribe_tracker(self, tracker):
        """Unsubcribe external engine client to completion events"""
        self._completion_trackers.remove(tracker)
        tracker.unregister(self)

    def _mark_load_branches_done(self):
        """Set status for all load branches as done
        (when all load branches are completed, power iteration
        worker thread is given permission to accept new power
        events)
        """
        self._current_power_iter = None
        self._notify_trackers(AllLoadBranchesDone)
        self._power_iter_queue.task_done()

    def _chain_power_events(self, volt_events, load_events=None):
        """Chain power events by dispatching input power events
        against children of the updated asset;
        Fire load events against parents of the updated asset if
        applicable;
        """

        print(self._current_power_iter)

        # reached the end of a stream of voltage updates
        if self._current_power_iter.num_volt_branches_active == 0:
            self._notify_trackers(AllVoltageBranchesDone)
            if self._current_power_iter.num_load_branches_active == 0:
                self._mark_load_branches_done()

        for child_key, event in volt_events:
            self.fire(event, self._assets[child_key])

        if load_events:
            for parent_key, event in load_events:
                self.fire(event, self._assets[parent_key])

    def _chain_load_events(self, load_events):
        """Chain load events"""

        print(self._current_power_iter)

        # load branches are completed
        if self._current_power_iter.num_load_branches_active == 0:
            self._mark_load_branches_done()

        if not load_events:
            return

        for asset_key, event in load_events:
            self.fire(event, self._assets[asset_key])

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

        if math.isclose(old_voltage, new_voltage):
            return

        volt_event = AssetPowerEvent(
            asset=None, old_out_volt=old_voltage, new_out_volt=new_voltage
        )

        self._power_iter_queue.put(PowerIteration(volt_event))

    def handle_state_update(self, asset_key, old_state, new_state):
        """Asset state changes to a new value,
        initiate a chain of power reactions
        Args:
            asset_key(int): key of the updated asset
            state(int): 0 for offline, 1 for online
        """

        if old_state == new_state:
            return

        updated_asset = self._assets[asset_key]
        out_volt = updated_asset.state.input_voltage

        volt_event = AssetPowerEvent(
            asset=updated_asset,
            old_out_volt=old_state * out_volt,
            new_out_volt=new_state * out_volt,
            old_state=old_state,
            new_state=new_state,
        )
        self._power_iter_queue.put(PowerIteration(volt_event))

    def handle_oid_update(self, asset_key, oid, value):
        pass

    def stop(self, code=None):
        self._power_iter_queue.put(None)
        self._worker_thread.join()
        self._sys_environ.stop()
        super().stop(code)

    # **Events are camel-case
    # pylint: disable=C0103,W0613
    def InputVoltageUpEvent_success(self, input_volt_event, asset_event):
        """Callback called if InputVoltageUpEvent was handled by the child asset
        """
        self._chain_power_events(
            *self._current_power_iter.process_power_event(asset_event)
        )

    def InputVoltageDownEvent_success(self, input_volt_event, asset_event):
        """Callback called if InputVoltageDown was handled by the child asset
        """
        self._chain_power_events(
            *self._current_power_iter.process_power_event(asset_event)
        )

    def ChildLoadUpEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load event that had
        happened to its child"""
        self._chain_load_events(
            self._current_power_iter.process_load_event(asset_load_event)
        )

    def ChildLoadDownEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load event that had
        happened to its child"""
        self._chain_load_events(
            self._current_power_iter.process_load_event(asset_load_event)
        )
