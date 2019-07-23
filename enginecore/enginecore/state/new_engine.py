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

from enginecore.state.state_initializer import initialize, clear_temp
from enginecore.state.engine_data_source import HardwareGraphDataSource
from enginecore.state.power_iteration import PowerIteration, ThermalIteration
from enginecore.state.power_events import AssetPowerEvent, SNMPEvent, AmbientEvent


class AllThermalBranchesDone(Event):
    """Dispatched when all hardware assets finish
    processing an ambient event"""


class AllVoltageBranchesDone(Event):
    """Dispatched when power iteration finishes downstream
    voltage event propagation to all the leaf nodes that 
    are descendants of the iteration source event"""

    success = True


class AllLoadBranchesDone(Event):
    """Dispatched when power iteration finishes upstream
    load event propagation across all load branches"""

    success = True


class EngineEventConsumer:
    """This wrapper watches an event queue in a separate thread
    and launches a processing iteration (e.g. a chain of power events
    that occured due to power outage)"""

    def __init__(self, iteration_worker_name="unspecified"):

        # queue of engine events waiting to be processed
        self._event_queue = queue.Queue()
        # work-in-progress
        self._current_iteration = None
        self._worker_thread = None
        self._on_iteration_launched = None
        self._iteration_worker_name = iteration_worker_name

    @property
    def current_iteration(self):
        """Iteration that is in progress/not yet completed
        (e.g. power downstream update still going on)"""
        return self._current_iteration

    def start(self, on_iteration_launched=None):
        """Launches consumer thread
        Args:
            on_iteration_launched(callable): called when event queue returns
                                             new iteration
        """
        self._on_iteration_launched = on_iteration_launched

        # initialize processing thread
        self._worker_thread = threading.Thread(
            target=self._worker, name=self._iteration_worker_name
        )
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def stop(self):
        """Join consumer thread (stop processing power queued power iterations)"""
        self.queue_iteration(None)
        self._worker_thread.join()

    def queue_iteration(self, iteration):
        """Queue an iteration for later processing;
        it will get dequeued once current_iteration is completed
        Args:
            iteration(EngineIteration): to be queued, event consumer will stop
                                        if None is supplied
        """
        self._event_queue.put(iteration)

    def mark_iteration_done(self):
        """Complete an iteration (so it can process next event in a queue if 
        available)"""
        self._current_iteration = None
        self._event_queue.task_done()

    def _worker(self):
        """Consumer processing event queue, calls a callback supplied in
        start()"""

        while True:
            # new processing iteration/loop was initialized
            next_iter = self._event_queue.get()

            if not next_iter:
                return

            assert self._current_iteration is None

            self._current_iteration = next_iter
            launch_results = self._current_iteration.launch()

            if self._on_iteration_launched:
                self._on_iteration_launched(*launch_results)


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

    def __init__(self, force_snmp_init=True, data_source=HardwareGraphDataSource):
        super(Engine, self).__init__()

        ### Set-up WebSocket & Redis listener ###
        logging.info("Starting simengine daemon...")

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}

        self._completion_trackers = []

        self._sys_environ = ServerRoom().register(self)

        self._power_iter_handler = EngineEventConsumer("power_worker")
        self._thermal_iter_handler = EngineEventConsumer("thermal_worker")

        self._data_source = data_source
        PowerIteration.data_source = data_source
        ThermalIteration.data_source = data_source

        # Register assets and reset power state
        self.reload_model(force_snmp_init)
        logging.info("Physical Environment:\n%s", self._sys_environ)

    def reload_model(self, force_snmp_init=True):
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

        self._power_iter_handler.start(on_iteration_launched=self._chain_power_events)
        self._thermal_iter_handler.start(
            on_iteration_launched=self._chain_thermal_events
        )

    @property
    def assets(self):
        """Hardware assets that are present in the system topology"""
        return self._assets

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
        self._notify_trackers(AllLoadBranchesDone)
        self._power_iter_handler.mark_iteration_done()

    def _chain_power_events(self, volt_events, load_events=None):
        """Chain power events by dispatching input power events
        against children of the updated asset;
        Fire load events against parents of the updated asset if
        applicable;
        """

        # reached the end of a stream of voltage updates
        if self._power_iter_handler.current_iteration.all_voltage_branches_done:
            self._notify_trackers(AllVoltageBranchesDone)
            if self._power_iter_handler.current_iteration.all_load_branches_done:
                self._mark_load_branches_done()

        for child_key, event in volt_events:
            self.fire(event, self._assets[child_key])

        if load_events:
            for parent_key, event in load_events:
                self.fire(event, self._assets[parent_key])

    def _chain_load_events(self, load_events):
        """Chain load events by dispatching more load events against
        parents of the updated child asset"""

        # load & voltage branches are completed
        if self._power_iter_handler.current_iteration.iteration_done:
            self._mark_load_branches_done()

        if not load_events:
            return

        for asset_key, event in load_events:
            self.fire(event, self._assets[asset_key])

    def _chain_thermal_events(self, thermal_events):
        """Chain thermal events by dispatching them against assets"""

        if self._thermal_iter_handler.current_iteration.iteration_done:
            self._notify_trackers(AllThermalBranchesDone)

        if not thermal_events:
            return

        for asset_key, event in thermal_events:
            self.fire(event, self._assets[asset_key])

    def handle_ambient_update(self, old_temp, new_temp):
        """Ambient changes to a new value, initiate a chain of thermal reactions
        Args:
            old_temp(float): old room temperature
            new_temp(float): new room temperature
        """
        self._thermal_iter_handler.queue_iteration(
            ThermalIteration(AmbientEvent(old_temp=old_temp, new_temp=new_temp))
        )

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

        self._power_iter_handler.queue_iteration(PowerIteration(volt_event))

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
        self._power_iter_handler.queue_iteration(PowerIteration(volt_event))

    def handle_oid_update(self, asset_key, oid, value):
        """React to OID update in redis store 
        Args:
            asset_key(int): key of the asset oid belongs to
            oid(str): updated oid
            value(str): OID value in snmpsim format "datatype|value"
        """
        if asset_key not in self._assets:
            logging.warning("Asset [%s] does not exist!", asset_key)
            return

        affected_asset_key, oid_details = self._data_source.get_asset_oid_info(
            asset_key, oid
        )

        if not oid_details:
            logging.warning(
                "OID:[%s] for asset:[%s] cannot be processed by engine!", oid, asset_key
            )
            return

        snmp_event = SNMPEvent(
            asset=self._assets[affected_asset_key],
            oid=oid,
            oid_value_name=oid_details["name"],
            oid_name=oid_details["specs"][value],
        )

        self._power_iter_handler.queue_iteration(PowerIteration(snmp_event))

    def stop(self, code=None):
        self._power_iter_handler.stop()
        self._thermal_iter_handler.stop()
        self._sys_environ.stop()

        for asset_key in self._assets:
            self._assets[asset_key].stop()

        HardwareGraphDataSource.cache_clear_all()
        super().stop(code)

    # **Events are camel-case
    # pylint: disable=C0103,W0613
    def InputVoltageUpEvent_success(self, input_volt_event, asset_event):
        """Callback called when InputVoltageUpEvent was handled by the asset
        affected by the input change
        """
        self._chain_power_events(
            *self._power_iter_handler.current_iteration.process_power_event(asset_event)
        )

    def InputVoltageDownEvent_success(self, input_volt_event, asset_event):
        """Callback called when InputVoltageDown was handled by the asset
        affected by the input change
        """
        self._chain_power_events(
            *self._power_iter_handler.current_iteration.process_power_event(asset_event)
        )

    # def SignalDown_success(self, evt, event_result):
    #     """When asset is powered down """
    #     self._power_success(event_result)

    # def SignalUp_success(self, evt, event_result):
    #     """When asset is powered up """
    #     self._power_success(event_result)

    def ChildLoadUpEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load incease event that had
        happened to its child"""
        self._chain_load_events(
            self._power_iter_handler.current_iteration.process_load_event(
                asset_load_event
            )
        )

    def ChildLoadDownEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load drop event that had
        happened to its child"""
        self._chain_load_events(
            self._power_iter_handler.current_iteration.process_load_event(
                asset_load_event
            )
        )

    def AmbientDownEvent_success(self, ambient_event, asset_thermal_event):
        """When asset is powered down """
        self._chain_thermal_events(
            self._thermal_iter_handler.current_iteration.process_thermal_event(
                asset_thermal_event
            )
        )

    def AmbientUpEvent_success(self, ambient_event, asset_thermal_event):
        """When asset is powered up """
        self._chain_thermal_events(
            self._thermal_iter_handler.current_iteration.process_thermal_event(
                asset_thermal_event
            )
        )
