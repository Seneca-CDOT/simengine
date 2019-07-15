import functools
from circuits import Component, Event, Worker, Debugger, handler


class PowerEvent(Event):
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


class EventDataPair:
    """A tiny utility that helps keep track of value changes due to some event
    (old & new values).
    """

    def __init__(self, old_value=None, new_value=None, is_valid_value=None):
        self._old_value, self._new_value = old_value, new_value
        self._is_valid_value = is_valid_value

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
        self._old_value = value

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
        self._new_value = value

    def unchanged(self):
        """Returns true if event did not affect state"""
        return self.old == self.new


class LoadEventDataPair(EventDataPair):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "target" not in kwargs or not kwargs["target"]:
            raise ValueError("Provided target value is invalid")
        self._target = kwargs["target"]

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value


class AssetPowerEvent(PowerEvent):
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


class InputVoltageEvent(PowerEvent):
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
        return self._source_asset.key if self._source_asset else 0

    def get_next_power_event(self, target_asset=None):
        """Get next power event (hardware asset event) that
        was caused by this input voltage change"""

        if target_asset:
            old_out_volt = target_asset.state.output_voltage
        else:
            old_out_volt = self._in_volt.old

        volt_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=old_out_volt,
            new_out_volt=self._in_volt.new,
            power_iter=self.power_iter,
            branch=self.branch,
        )

        volt_event.state.old = target_asset.state.status

        return volt_event


class InputVoltageUpEvent(InputVoltageEvent):
    """Voltage event that gets dispatched against assets
    (when input voltage to the asset spikes)"""


class InputVoltageDownEvent(InputVoltageEvent):
    """Voltage event that gets dispatched against assets
    (when input voltage to the asset drops)"""


class LoadEvent(PowerEvent):
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
        """Load changes associated with the event"""
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
