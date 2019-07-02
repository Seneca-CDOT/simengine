import logging

import functools
import queue
import threading

from circuits import Component, Event, Worker, Debugger, handler
from circuits import Event

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.hardware.room import ServerRoom, Asset

from enginecore.tools.recorder import RECORDER
from enginecore.state.api import ISystemEnvironment
from enginecore.state.net.ws_server import WebSocket
from enginecore.state.net.ws_requests import ServerToClientRequests

from enginecore.state.state_initializer import initialize, clear_temp, configure_env
from enginecore.state.engine_data_source import HardwareGraphDataSource


class PowerEvent(Event):
    """Aggregates voltage event"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._power_iter = kwargs["power_iter"] if "power_iter" in kwargs else None
        self._branch = kwargs["branch"] if "branch" in kwargs else None

    @property
    def power_iter(self):
        """Power iteration power event belongs to"""
        return self._power_iter

    @power_iter.setter
    def power_iter(self, value):
        self._power_iter = value

    @property
    def branch(self):
        """Voltage branch"""
        return self._branch

    @branch.setter
    def branch(self, value):
        self._branch = value


class AssetVoltageEvent(PowerEvent):
    """Voltage power event associated with a particular asset"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        required_args = ["asset", "new_out_volt", "old_out_volt"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._asset = kwargs["asset"]
        self._new_out_volt = kwargs["new_out_volt"]
        self._old_out_volt = kwargs["old_out_volt"]

        # populate optional state updates
        self._new_state = kwargs["new_state"] if "new_state" in kwargs else None
        self._old_state = kwargs["old_state"] if "old_state" in kwargs else None

    def get_next_power_event(self):
        """Returns next event that will be dispatched against children of 
        the source asset
        """

        if self._old_out_volt > self._new_out_volt or self._new_out_volt == 0:
            volt_event = InputVoltageDownEvent
        else:
            volt_event = InputVoltageUpEvent

        print("\n\nBRANCH")
        print(self._branch)

        next_event = volt_event(
            old_in_volt=self._old_out_volt,
            new_in_volt=self._new_out_volt,
            source_asset=self._asset,
            power_iter=self.power_iter,
            branch=self._branch,
        )

        return next_event


class InputVoltageEvent(PowerEvent):
    success = True

    def get_next_power_event(self, source_e_result):

        print("\n\nBRANCH INV")
        print(self._branch)

        volt_event = AssetVoltageEvent(
            **source_e_result, power_iter=self.power_iter, branch=self.branch
        )

        return volt_event


class InputVoltageUpEvent(InputVoltageEvent):
    pass


class InputVoltageDownEvent(InputVoltageEvent):
    pass


class ChildLoadUpEvent(Event):
    pass


class ChildLoadDownEvent(Event):
    pass


class AllVoltageBranchesDone(Event):
    success = True


class VoltageBranch:
    def __init__(self, src_event, power_iter):
        self._src_event = src_event
        self._src_event.branch = self
        self._power_iter = power_iter

    @property
    def src_event(self):
        """Get root node/root access of the voltage branch"""
        return self._src_event

    def __call__(self):
        return self.src_event


class PowerIteration:

    data_source = None

    def __init__(self, src_event):
        """Source """
        self._volt_branches_active = []
        self._volt_branches_done = []

        self._last_processed_volt_event = None

        self._src_event = src_event
        self._src_event.power_iter = self

    def __str__(self):
        return (
            "Power Iteration due to incoming event:\n"
            " | {0._src_event}\n"
            "Loop Details:\n"
            " | Number Voltage Branches in-progress: {0.num_volt_branches_active}\n"
            " | Number Voltage Branches completed: {0.num_volt_branches_done}\n"
            " | Last Processed Power Event: \n"
            " | {0._last_processed_volt_event}\n"
        ).format(self)

    @property
    def num_volt_branches_active(self):
        """Number of voltage branches/streams still in progress"""
        return len(self._volt_branches_active)

    @property
    def num_volt_branches_done(self):
        """Number of voltage branches/streams still in progress"""
        return len(self._volt_branches_done)

    def complete_volt_branch(self, branch: VoltageBranch):
        """Remove branch from a list of completed branches"""
        self._volt_branches_active.remove(branch)
        self._volt_branches_done.append(branch)

    def launch(self):
        """Start up power iteration by returning events
        Returns:
            tuple consisting of:
                - ParentAssetVoltageEvent (either up or down)
                - ChildLoadEvent     (either up or down)
        """
        return self.process_power_event(self._src_event)

    def process_power_event(self, event):
        """Retrieves events as a reaction to the passed source event"""

        logging.info(" \n\nProcessing event branch %s", event.branch)
        self._last_processed_volt_event = event

        # asset caused by power loop (individual asset power update)
        if event.kwargs["asset"]:
            return self._process_hardware_asset_event(event)

        # wallpower voltage caused power loop
        return self._process_wallpower_event(event)

    def _process_wallpower_event(self, event):
        """Wall-power voltage was updated, retrieve chain events associated
        with mains-powered outlets
        """
        wp_outlets = self.data_source.get_mains_powered_assets()

        new_branches = [VoltageBranch(event, self) for _ in wp_outlets]
        self._volt_branches_active.extend(new_branches)

        return (
            [
                (k, b.src_event.get_next_power_event())
                for k, b in zip(wp_outlets, new_branches)
            ],
            None,
        )

    def _process_hardware_asset_event(self, event):
        """One of the hardware assets went online/online"""

        child_keys, parent_keys = self.data_source.get_affected_assets(
            event.kwargs["asset"].key
        )

        if not event.branch:
            self._volt_branches_active.append(VoltageBranch(event, self))

        events = [event.get_next_power_event()]

        # forked branch -> replace it with 'n' child voltage branches
        if len(child_keys) > 1:
            new_branches = [
                VoltageBranch(event.get_next_power_event(), self) for _ in child_keys
            ]
            self._volt_branches_active.extend(new_branches)
            events = [b.src_event for b in new_branches]

        # delete voltage branch (power stream) when it forks
        # or when it reaches leaf asset/node
        if (len(child_keys) > 1 and event.branch) or not child_keys:
            self.complete_volt_branch(event.branch)

        return (zip(child_keys, events), None)


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
            self.fire(AllVoltageBranchesDone(), comp_tracker)

    def subscribe_tracker(self, tracker):
        """Subcribe external engine client to completion events"""
        self._completion_trackers.append(tracker.register(self))

    def unsubscribe_tracker(self, tracker):
        """Unsubcribe external engine client to completion events"""
        self._completion_trackers.remove(tracker)
        tracker.unregister(self)

    def _chain_power_events(self, volt_events, load_events=None):

        print(self._current_power_iter)

        # reached the end of a stream of voltage updates
        # TODO: when load is implemented, move this to load completion
        if self._current_power_iter.num_volt_branches_active == 0:
            self._current_power_iter = None
            self._notify_trackers(None)
            self._power_iter_queue.task_done()

        for asset_key, event in volt_events:
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

        volt_event = AssetVoltageEvent(
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
        out_volt = updated_asset.state.output_voltage

        volt_event = AssetVoltageEvent(
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
        super().stop(code)

        self._power_iter_queue.put(None)
        self._worker_thread.join()
        self._sys_environ.stop()

    # **Events are camel-case
    # pylint: disable=C0103,W0613

    def _on_power_event_success(self, evt, e_results):
        """Chain power events"""

        power_event = evt.get_next_power_event(
            {
                "asset": self._assets[e_results["key"]],
                **e_results["voltage"],
                **e_results["state"],
            }
        )

        self._chain_power_events(*evt.power_iter.process_power_event(power_event))

    def InputVoltageUpEvent_success(self, evt, e_results):
        """Callback called if InputVoltageUpEvent was handled by the child asset
        """
        self._on_power_event_success(evt, e_results)

    def InputVoltageDownEvent_success(self, evt, e_results):
        """Callback called if InputVoltageDown was handled by the child asset
        """
        self._on_power_event_success(evt, e_results)
