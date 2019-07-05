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

    @new.setter
    def new(self, value):
        if self._is_valid_value and not self._is_valid_value(value):
            raise ValueError("Provided event data value is invalid")
        self._new_value = value


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

        if "new_state" in kwargs and "old_state" in kwargs:
            self._state = EventDataPair(kwargs["old_state"], kwargs["new_state"])
        else:
            self._state = EventDataPair()

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

    def get_next_voltage_event(self):
        """Returns next event that will be dispatched against children of 
        the source asset
        """
        out_volt = self.out_volt

        if out_volt.old > out_volt.new or out_volt.new == 0:
            volt_event = InputVoltageDownEvent
        else:
            volt_event = InputVoltageUpEvent

        next_event = volt_event(
            old_in_volt=out_volt.old,
            new_in_volt=out_volt.new,
            source_asset=self._asset,
            power_iter=self.power_iter,
            branch=self._branch,
        )

        return next_event


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

        self._new_in_volt = kwargs["new_in_volt"]
        self._old_in_volt = kwargs["old_in_volt"]

        self._source_asset = (
            kwargs["source_asset"] if "source_asset" in kwargs else None
        )

    def get_next_power_event(self, target_asset=None):
        volt_event = AssetPowerEvent(
            asset=target_asset,
            old_out_volt=self._old_in_volt,
            new_out_volt=self._new_in_volt,
            power_iter=self.power_iter,
            branch=self.branch,
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
