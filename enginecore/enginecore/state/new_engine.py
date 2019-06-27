import logging
import os
import math

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

from enginecore.state.state_initializer import initialize, clear_temp
from enginecore.state.engine_data_source import HardwareGraphDataSource


class VoltageEvent(Event):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        required_args = ["asset", "new_out_volt", "old_out_volt"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._asset = kwargs["asset"]
        self._new_out_volt = kwargs["new_out_volt"]
        self._old_out_volt = kwargs["old_out_volt"]

    def get_next_power_event(self):
        """Returns next event that will be dispatched against children of 
        the source asset
        """

        if self._old_out_volt > self._new_out_volt or self._new_out_volt == 0:
            volt_event = InputVoltageDownEvent
        else:
            volt_event = InputVoltageUpEvent

        next_event = volt_event(
            old_in_volt=self._old_out_volt,
            new_in_volt=self._new_out_volt,
            source_asset=self._asset,
        )

        next_event.power_iter = self.power_iter
        next_event.branch = self.branch

        return next_event

    def with_state_update(self, old_state=None, new_state=None):

        if old_state is None or new_state is None or old_state == new_state:
            return self

        self.kwargs["old_state"] = old_state
        self.kwargs["new_state"] = new_state
        return self

    def with_load_update(self, old_load=None, new_load=None):

        if old_load is None or new_load is None or old_load == new_load:
            return self

        self.kwargs["old_load"] = old_load
        self.kwargs["new_load"] = new_load
        return self


class InputVoltageUpEvent(Event):
    success = True

    def get_next_power_event(self, source_e_result):

        volt_event = VoltageEvent(**source_e_result)

        volt_event.power_iter = self.power_iter
        volt_event.branch = self.branch

        return volt_event


class InputVoltageDownEvent(Event):
    success = True

    def get_next_power_event(self, source_e_result):
        volt_event = VoltageEvent(**source_e_result)

        volt_event.power_iter = self.power_iter
        volt_event.branch = self.branch

        return volt_event


class ChildLoadUpEvent(Event):
    pass


class ChildLoadDownEvent(Event):
    pass


class VoltageBranchCompleted(Event):
    success = True


class VoltageBranch:
    def __init__(self, src_event, power_iter):
        self._src_event = src_event

        self._src_event.power_iter = power_iter
        self._src_event.branch = self

        self._completed = False

        self._power_iter = power_iter

    @property
    def src_event(self):
        return self._src_event

    @property
    def branch_completed(self):
        return self._completed

    def __call__(self):
        return self.src_event


class PowerIteration:

    data_source = None

    def __init__(self, src_event):
        """Source """
        self._voltage_branches = [VoltageBranch(src_event, self)]

    def launch(self):
        """Start up power iteration by returning events
        Returns:
            tuple consisting of:
                - ParentVoltageEvent (either up or down)
                - ChildLoadEvent     (either up or down)
        """

        logging.info("SRC EVENT: %s", self._voltage_branches[0]())
        return self.process_power_event(self._voltage_branches[0]())

    def process_power_event(self, event):

        logging.info(" \n\nProcessing event branch %s", event.branch)

        # asset caused power loop
        if event.kwargs["asset"]:
            return self._process_hardware_asset_event(event)

        # wallpower voltage caused power loop
        return self._process_wallpower_event(event)

    def _process_wallpower_event(self, event: VoltageEvent):
        """Wall-power voltage was updated"""
        wall_power_out_keys = self.data_source.get_mains_powered_assets()

        return ((wall_power_out_keys, event.get_next_power_event()), None)

    def _process_hardware_asset_event(self, event: VoltageEvent):
        """One of the hardware assets went online/online"""

        child_keys, parent_keys = self.data_source.get_affected_assets(
            event.kwargs["asset"].key
        )

        # if len(child_keys) > 1:
        #     self._voltage_branches.remove(event.branch)

        # for c_key in child_keys:
        #     self._voltage_branches.append(
        #         VoltageBranch(event.get_next_power_event(), self)
        #     )

        return ((child_keys, event.get_next_power_event()), None)


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
        """Consumer processing power event queue"""

        while True:
            # new power-loop was initialized
            next_power_iter = self._power_iter_queue.get()
            logging.info("--------------------")
            logging.info("New power iteration")
            logging.info("--------------------")

            self._chain_power_events(*next_power_iter.launch())
            self._power_iter_queue.task_done()

    def subscribe_tracker(self, tracker):
        self._completion_trackers.append(tracker.register(self))

    def unsubscribe_tracker(self, tracker):
        self._completion_trackers.remove(tracker)
        tracker.unregister(self)

    def _chain_power_events(self, volt_events, load_events=None):

        child_keys, event = volt_events

        if not child_keys:
            for volt_sub in self._completion_trackers:
                self.fire(VoltageBranchCompleted(branch=event.branch), volt_sub)

        for asset_key in child_keys:
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

        volt_event = VoltageEvent(
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

        out_volt = self._assets[asset_key].state.output_voltage

        volt_event = VoltageEvent(
            asset=self._assets[asset_key],
            old_out_volt=old_state * out_volt,
            new_out_volt=new_state * out_volt,
        ).with_state_update(old_state=old_state, new_state=new_state)

        self._power_iter_queue.put(PowerIteration(volt_event))

    def handle_oid_update(self, asset_key, oid, value):
        pass

    # **Events are camel-case
    # pylint: disable=C0103,W0613

    def _on_power_event_success(self, evt, e_results):
        """Chain power events"""

        power_event = evt.get_next_power_event(
            {"asset": self._assets[e_results["key"]], **e_results["voltage"]}
        ).with_state_update(**e_results["state"])

        logging.info("power event result on voltage update: %s", power_event)
        self._chain_power_events(*evt.power_iter.process_power_event(power_event))

    def InputVoltageUpEvent_success(self, evt, e_results):
        """Callback called if InputVoltageUpEvent was handled by the child asset
        """

        logging.info("Parent voltage up event succeeded ")
        self._on_power_event_success(evt, e_results)

    def InputVoltageDownEvent_success(self, evt, e_results):
        """Callback called if InputVoltageDown was handled by the child asset
        """

        logging.info("Parent voltage down event succeeded ")
        self._on_power_event_success(evt, e_results)
