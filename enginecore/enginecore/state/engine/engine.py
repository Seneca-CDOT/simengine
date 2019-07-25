import logging

import math
from circuits import Component, Event

from enginecore.state.hardware.room import ServerRoom, Asset
from enginecore.tools.recorder import RECORDER
from enginecore.state.api import ISystemEnvironment
from enginecore.state.state_initializer import initialize, clear_temp

from enginecore.state.engine.iteration import PowerIteration, ThermalIteration
from enginecore.state.engine.iteration_consumer import EngineIterationConsumer
from enginecore.state.engine.data_source import HardwareGraphDataSource
from enginecore.state.engine.events import (
    AssetPowerEvent,
    SNMPEvent,
    AmbientEvent,
    MainsPowerEvent,
)


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

        # completion trackers will be notified of events happening in the system
        self._completion_trackers = []

        self._sys_environ = ServerRoom().register(self)

        # track iterations (thermal/power) in separate threads
        self._power_iter_handler = EngineIterationConsumer("power_worker")
        self._thermal_iter_handler = EngineIterationConsumer("thermal_worker")

        data_source.init_connection()

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
            self.fire(event, comp_tracker)

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
        self._notify_trackers(AllLoadBranchesDone())
        self._power_iter_handler.mark_iteration_done()

    def _chain_power_events(self, volt_events, load_events=None):
        """Chain power events by dispatching input power events
        against children of the updated asset;
        Fire load events against parents of the updated asset if
        applicable;
        """

        # reached the end of a stream of voltage updates
        if self._power_iter_handler.current_iteration.all_voltage_branches_done:
            self._notify_trackers(AllVoltageBranchesDone())
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
            self._notify_trackers(AllThermalBranchesDone())
            self._thermal_iter_handler.mark_iteration_done()

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
        amb_event = AmbientEvent(old_temp=old_temp, new_temp=new_temp)
        self._notify_trackers(amb_event)

        self._thermal_iter_handler.queue_iteration(ThermalIteration(amb_event))

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
        self._notify_trackers(volt_event)
        if math.isclose(old_voltage, 0.0) or math.isclose(new_voltage, 0.0):
            self._notify_trackers(
                MainsPowerEvent(mains=int(math.isclose(old_voltage, 0.0)))
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

        self._notify_trackers(volt_event)
        self._power_iter_handler.queue_iteration(PowerIteration(volt_event))

    def handle_oid_update(self, asset_key, oid, value):
        """React to OID update
        Args:
            asset_key(int): key of the asset oid belongs to
            oid(str): updated oid
            value(str): OID value
        """
        if asset_key not in self._assets:
            logging.warning("Asset [%s] does not exist!", asset_key)
            return

        # get asset key associated with the oid & oid details
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
            oid_value_name=oid_details["specs"][value],
            oid_name=oid_details["name"],
        )

        self._power_iter_handler.queue_iteration(PowerIteration(snmp_event))

    def stop(self, code=None):
        """Cleanup threads/hardware assets"""
        self._power_iter_handler.stop()
        self._thermal_iter_handler.stop()
        self._sys_environ.stop()

        for asset_key in self._assets:
            self._assets[asset_key].stop()

        HardwareGraphDataSource.cache_clear_all()
        HardwareGraphDataSource.close()

        super().stop(code)

    # Chain events processed by the hardware assets (e.g. by dispatching next events)
    # (these callbacks are called by circuit when an
    # asset finishes processing incoming eent)

    def _on_asset_power_event_success(self, asset_event):
        """Notify current power iteration that hardware asset
        finished processing power event"""
        self._notify_trackers(asset_event)
        self._chain_power_events(
            *self._power_iter_handler.current_iteration.process_power_event(asset_event)
        )

    def _on_asset_load_event_success(self, asset_event):
        """Notify current power iteration that hardware asset
        finished processing load event"""
        self._notify_trackers(asset_event)
        self._chain_load_events(
            self._power_iter_handler.current_iteration.process_load_event(asset_event)
        )

    def _on_asset_thermal_event_success(self, asset_event):
        """Notify current thermal iteration that hardware asset
        finished processing thermal changes"""
        self._chain_thermal_events(
            self._thermal_iter_handler.current_iteration.process_thermal_event(
                asset_event
            )
        )

    # **Events are camel-case
    # pylint: disable=C0103,W0613
    def InputVoltageUpEvent_success(self, input_volt_event, asset_event):
        """Callback called when InputVoltageUpEvent was handled by the asset
        affected by the input change
        """
        self._on_asset_power_event_success(asset_event)

    def InputVoltageDownEvent_success(self, input_volt_event, asset_event):
        """Callback called when InputVoltageDown was handled by the asset
        affected by the input change
        """
        self._on_asset_power_event_success(asset_event)

    def SignalDownEvent_success(self, signal_event, asset_event):
        """When asset is powered down through network interface"""
        self._on_asset_power_event_success(asset_event)

    def SignalUpEvent_success(self, signal_event, asset_event):
        """When asset is powered up through network interface"""
        self._on_asset_power_event_success(asset_event)

    def ChildLoadUpEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load incease event that had
        happened to its child"""
        self._on_asset_load_event_success(asset_load_event)

    def ChildLoadDownEvent_success(self, child_load_event, asset_load_event):
        """Callback called when asset finishes processing load drop event that had
        happened to its child"""
        self._on_asset_load_event_success(asset_load_event)

    def AmbientDownEvent_success(self, ambient_event, asset_thermal_event):
        """When asset is powered down """
        self._on_asset_thermal_event_success(asset_thermal_event)

    def AmbientUpEvent_success(self, ambient_event, asset_thermal_event):
        """When asset is powered up """
        self._on_asset_thermal_event_success(asset_thermal_event)