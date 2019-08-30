"""Engine events are passed back and forth between the engine & hardware assets
Engine typically dispatches events associated with the parents/children state changes
to the target assets;
Whereas assets return events that had happened to them (e.g. if asset load was updated
due to voltage change etc.)
"""
import functools
from circuits import Event


class EventDataPair:
    """A tiny utility that helps keep track of value changes due to some event
    (old & new values).
    """

    def __init__(self, *args, **kwargs):
        self._old_value, self._new_value = args if len(args) == 2 else (None, None)

        self._is_valid_value = (
            kwargs["is_valid_value"] if "is_valid_value" in kwargs else None
        )

    def __call__(self):
        return self._old_value, self._new_value

    def __str__(self):
        return "data changed as: '{0.old}'->'{0.new}'".format(self)

    @property
    def old(self):
        """Value before the event took place"""
        return self._old_value

    @old.setter
    def old(self, value):
        if self._is_valid_value and not self._is_valid_value(value):
            raise ValueError("Provided event data value is invalid")
        self._old_value = max(0, value)

    @property
    def new(self):
        """New value caused by the event"""
        return self._new_value

    @property
    def difference(self):
        """Difference between new & old value"""
        return self._new_value - self._old_value

    @new.setter
    def new(self, value):
        if self._is_valid_value and not self._is_valid_value(value):
            raise ValueError("Provided event data value is invalid")
        self._new_value = max(0, value)

    def unchanged(self):
        """Returns true if event did not affect state"""
        return self.old == self.new or self.new is None


class EngineEvent(Event):
    """Power event within an engine that is associated with 
    a power iteration (see PowerIteration)
    and power branch (Either VoltageBranch or LoadBranch)
    """

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
        """Power branch (graph path of power flow)"""
        return self._branch

    @branch.setter
    def branch(self, value):
        self._branch = value


class BatteryEvent(EngineEvent):
    """Event occuring due to UPS battery update"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_args = ["old_battery", "new_battery", "asset"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._battery = EventDataPair(kwargs["old_battery"], kwargs["new_battery"])
        self._asset = kwargs["asset"]

    @property
    def battery(self):
        """Battery level change associated with this event"""
        return self._battery

    @property
    def asset(self):
        """UPS asset battery belongs to"""
        return self._asset


class MainsPowerEvent(EngineEvent):
    """Event associated with power outage or power restoration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "mains" not in kwargs:
            raise KeyError("Mains state is missing")
        self._mains = EventDataPair(kwargs["mains"] ^ 1, kwargs["mains"])

    @property
    def mains(self):
        """Indicates wallpower state change"""
        return self._mains


class PowerButtonEvent(EngineEvent):
    """Asset's power state changed due to user turning asset off/on"""

    success = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_args = ["old_state", "new_state", "asset"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._state = EventDataPair(kwargs["old_state"], kwargs["new_state"])
        self._asset = kwargs["asset"]

    @property
    def state(self):
        """Retrieve state changes due to user pressing power button"""
        return self._state

    @property
    def asset(self):
        """hardware asset this event occurred to"""
        return self._asset

    def get_next_power_event(self):
        """Get next power event that has occurred due to user "pressing"
        power button"""
        out_volt = {
            0: self._asset.state.input_voltage,
            1: self._asset.state.output_voltage,
        }[self.state.new]

        return AssetPowerEvent(
            asset=self._asset,
            old_out_volt=self.state.old * out_volt,
            new_out_volt=self.state.new * out_volt,
            old_state=self.state.old,
            new_state=self.state.new,
            power_iter=self.power_iter,
            branch=self._branch,
        )


class PowerButtonOnEvent(PowerButtonEvent):
    """Asset was powered on by a user"""


class PowerButtonOffEvent(PowerButtonEvent):
    """Asset was powered off by a user"""


class SignalEvent(EngineEvent):
    """Asset was signaled to update its power state through network interface"""

    success = True


class SignalDownEvent(SignalEvent):
    """Asset was signaled to shut down through network"""

    def get_next_power_event(self, target_asset):
        """Get next power event (hardware asset event) that
        was caused by a signal"""

        asset_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=target_asset.state.output_voltage,
            new_out_volt=0,
            power_iter=self.power_iter,
            branch=self.branch,
        )

        asset_event.state.old = target_asset.state.status
        asset_event.state.new = 0

        return asset_event


class SignalUpEvent(SignalEvent):
    """Asset was signaled to power up through network"""

    def get_next_power_event(self, target_asset):
        """Get next power event (hardware asset event) that
        was caused by a signal"""

        asset_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=target_asset.state.output_voltage,
            new_out_volt=target_asset.state.input_voltage,
            power_iter=self.power_iter,
            branch=self.branch,
        )

        asset_event.state.old = target_asset.state.status
        asset_event.state.new = 1

        return asset_event


class SignalRebootEvent(SignalEvent):
    """Asset was signaled to reboot through network"""

    def get_next_power_event(self, target_asset):
        """Get next power event (hardware asset event) that
        was caused by a signal"""

        asset_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=target_asset.state.output_voltage,
            new_out_volt=target_asset.state.output_voltage,
            power_iter=self.power_iter,
            branch=self.branch,
        )

        asset_event.state.old = target_asset.state.status
        asset_event.state.new = target_asset.state.status

        return asset_event


class AmbientEvent(EngineEvent):
    """Ambient has changed (room temerature within the server enclosure)"""

    success = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_args = ["old_temp", "new_temp"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._temp = EventDataPair(kwargs["old_temp"], kwargs["new_temp"])

    @property
    def temperature(self):
        """Retrieve temperature change"""
        return self._temp

    def get_next_thermal_event(self):
        """Get next event to be dispatched against server hardware"""

        ambient_event = (
            AmbientUpEvent if self.temperature.difference > 0 else AmbientDownEvent
        )
        return ambient_event(
            power_iter=self.power_iter,
            branch=self._branch,
            old_temp=self.temperature.old,
            new_temp=self.temperature.new,
        )


class AmbientUpEvent(AmbientEvent):
    """Ambient went up"""

    success = True


class AmbientDownEvent(AmbientEvent):
    """Ambient went down"""

    success = True


class SNMPEvent(EngineEvent):
    """SNMP event is triggered when a value under certain SNMP oid gets changed"""

    STATE_SPECS = {
        "OutletState": {
            "switchOff": SignalDownEvent,
            "switchOn": SignalUpEvent,
            "immediateReboot": SignalRebootEvent,
            "delayedOff": functools.partial(SignalDownEvent, delayed=True),
            "delayedOn": functools.partial(SignalUpEvent, delayed=True),
        },
        "PowerOff": {
            "switchOff": SignalDownEvent,
            "switchOffGraceful": functools.partial(SignalDownEvent, graceful=True),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_args = ["asset", "oid", "oid_value_name", "oid_name"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._asset = kwargs["asset"]
        self._oid = kwargs["oid"]
        self._oid_value_name = kwargs["oid_value_name"]
        self._oid_name = kwargs["oid_name"]

    @property
    def asset(self):
        """Asset associated with snmp object id (e.g. outlet controlled by oid)"""
        return self._asset

    @property
    def oid_value_name(self):
        """Abstract name of oid value given internally by the engine 
        (to ensure cross-vendor support)"""
        return self._oid_value_name

    @property
    def oid_name(self):
        """Abstract name of oid given internally by the engine"""
        return self._oid_name

    def get_next_signal_event(self):
        """Map OID & their values to events"""
        return SNMPEvent.STATE_SPECS[self.oid_name][self.oid_value_name](
            power_iter=self.power_iter, branch=self.branch
        )


class AssetPowerEvent(EngineEvent):
    """Asset power event aggregates 2 event types:
    Voltage & Load
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        required_args = ["asset", "new_out_volt", "old_out_volt"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._asset = kwargs["asset"]
        self._out_volt = EventDataPair(kwargs["old_out_volt"], kwargs["new_out_volt"])
        self._load = EventDataPair()
        self._streamed_load_upd = None

        if "new_state" in kwargs and "old_state" in kwargs:
            self._state = EventDataPair(kwargs["old_state"], kwargs["new_state"])
        else:
            self._state = EventDataPair()

    def __str__(self):
        event_type = "wallpower" if not self.asset else self.asset.key
        return (
            "[{}]::AssetPowerEvent: \n".format(event_type)
            + super().__str__()
            + "\n"
            + (
                " -- VoltageBranch: {0._branch} \n"
                " state update          : {0.state} \n"
                " output voltage update : {0.out_volt} \n"
                " load update           : {0.load} \n"
            ).format(self)
        )

    @property
    def asset(self):
        """Hardware asset that caused power event"""
        return self._asset

    @property
    def state(self):
        """Old/New asset state that resulted from a power event
        None: if asset state did not change"""
        return self._state

    @property
    def out_volt(self):
        """Old/New output voltage that resulted from a power event"""
        return self._out_volt

    @property
    def load(self):
        """Old/New load changes caused by a power event"""
        return self._load

    def calc_load_from_volt(self):
        """Sets load change based off old,  new load and asset's
        power consumption"""
        calc_load = functools.partial(AssetPowerEvent.calculate_load, self._asset.state)
        self._load = EventDataPair(
            *(calc_load(volt) for volt in [self.out_volt.old, self.out_volt.new])
        )

    @staticmethod
    def calculate_load(state, voltage):
        """Calculate asset load"""
        return state.power_consumption / voltage if voltage else 0

    def get_next_voltage_event(self):
        """Returns next event that will be dispatched against children of 
        the source asset
        """
        out_volt = self.out_volt

        if out_volt.old > out_volt.new or out_volt.new == 0:
            volt_event = InputVoltageDownEvent
        else:
            volt_event = InputVoltageUpEvent

        return volt_event(
            old_in_volt=out_volt.old,
            new_in_volt=out_volt.new,
            source_asset=self._asset,
            power_iter=self.power_iter,
            branch=self._branch,
        )

    def get_next_load_event(self):
        """Asset power event may result in load update
        (which needs to be propagated upstream)
        """

        if self.load.unchanged():
            return None

        load_event = (
            ChildLoadUpEvent if self.load.difference > 0 else ChildLoadDownEvent
        )

        return load_event(
            old_load=self.load.old,
            new_load=self.load.new,
            source_asset=self._asset,
            power_iter=self.power_iter,
            branch=self._branch,
        )

    @property
    def streamed_load_updates(self):
        """Streamed load updates have key assigned to them which
        indicates load-stream direction (e.g. used for servers which can have
        multiple power sources (PSUs))
        """
        return self._streamed_load_upd

    @streamed_load_updates.setter
    def streamed_load_updates(self, update):
        self._streamed_load_upd = update

    def streamed_load_event(self, pkey):
        """Get load event from stream load information
        stored in streamed_load_updates"""
        s_load = self._streamed_load_upd[pkey]
        if s_load.unchanged():
            return None

        load_event = ChildLoadUpEvent if s_load.difference > 0 else ChildLoadDownEvent

        return load_event(
            old_load=s_load.old,
            new_load=s_load.new,
            source_asset=self._asset,
            power_iter=self.power_iter,
            branch=self._branch,
        )


class InputVoltageEvent(EngineEvent):
    """Input Voltage drop/spike event dispatched against
    a particular hardware device
    """

    success = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_args = ["source_asset", "new_in_volt", "old_in_volt"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._in_volt = EventDataPair(kwargs["old_in_volt"], kwargs["new_in_volt"])
        self._source_asset = (
            kwargs["source_asset"] if "source_asset" in kwargs else None
        )

    @property
    def in_volt(self):
        """Old/New input voltage"""
        return self._in_volt

    @property
    def source_key(self):
        """Source key of the asset causing input voltage event"""
        return self._source_asset.key if self._source_asset else 0

    def get_next_power_event(self, target_asset=None):
        """Get next power event (hardware asset event) that
        was caused by this input voltage change"""

        if target_asset:
            old_out_volt = target_asset.state.output_voltage
        else:
            old_out_volt = self._in_volt.old

        asset_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=old_out_volt,
            new_out_volt=self._in_volt.new,
            power_iter=self.power_iter,
            branch=self.branch,
        )

        asset_event.state.old = target_asset.state.status

        return asset_event


class InputVoltageUpEvent(InputVoltageEvent):
    """Voltage event that gets dispatched against assets
    (when input voltage to the asset spikes)"""


class InputVoltageDownEvent(InputVoltageEvent):
    """Voltage event that gets dispatched against assets
    (when input voltage to the asset drops)"""


class LoadEvent(EngineEvent):
    """Load event is emitted whenever there is load 
    change somewhere in the system (due to voltage changes or power updates)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_args = ["old_load", "new_load"]

        if not all(r_arg in kwargs for r_arg in required_args):
            raise KeyError("Needs arguments: " + ",".join(required_args))

        self._load = EventDataPair(kwargs["old_load"], kwargs["new_load"])

    @property
    def load(self):
        """Get load update (old/new values) associated with this event"""
        return self._load

    def __str__(self):
        return self._load.__str__()


class AssetLoadEvent(LoadEvent):
    """Asset load was updated"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "asset" not in kwargs or not kwargs["asset"]:
            raise KeyError("Needs arguments: asset")

        self._asset = kwargs["asset"]
        self._load.old = self._asset.state.load

    def get_next_load_event(self):
        """Get next load event that can be dispatched against asset powering this 
        device"""
        return (ChildLoadDownEvent if self._load.difference < 0 else ChildLoadUpEvent)(
            power_iter=self.power_iter,
            branch=self._branch,
            old_load=self._load.old,
            new_load=self._load.new,
        )

    @property
    def asset(self):
        """Hardware asset that caused power event"""
        return self._asset

    def __str__(self):
        return (
            "[{}]::AssetLoadEvent: \n ".format(self._asset.key)
            + " -- VoltageBranch: {} \n".format(self._branch)
            + super().__str__()
        )


class ChildLoadEvent(LoadEvent):
    """Event at child load changes"""

    success = True

    def get_next_load_event(self, target_asset):
        """Get next asset event resulted from
        load changes of the child asset 
        """
        return AssetLoadEvent(
            asset=target_asset,
            power_iter=self.power_iter,
            branch=self._branch,
            old_load=self._load.old,
            new_load=self._load.new,
        )


class ChildLoadUpEvent(ChildLoadEvent):
    """Child load went up, this is dispatched against parent
    to notify of load update"""


class ChildLoadDownEvent(ChildLoadEvent):
    """Child load was decreased, this is dispatched against parent
    to notify of load update"""
