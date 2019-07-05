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
        self._new_out_volt = kwargs["new_out_volt"]
        self._old_out_volt = kwargs["old_out_volt"]

        self._new_state, self._old_state = None, None

        if "new_state" in kwargs and "old_state" in kwargs:
            self.new_state = kwargs["new_state"]
            self.old_state = kwargs["old_state"]

    @property
    def asset(self):
        """Hardware asset that caused power event"""
        return self._asset

    @property
    def new_state(self):
        """New asset state that resulted from a power event
        None: if asset state did not change"""
        return self._new_state

    @new_state.setter
    def new_state(self, value):
        if value not in (0, 1):
            raise ValueError("Must be either 1 or 0")
        self._new_state = value

    @property
    def old_state(self):
        """Old asset power state (1 or 0), None if input voltage change did not 
        trigger state changes"""
        return self._old_state

    @old_state.setter
    def old_state(self, value):
        if value not in (0, 1):
            raise ValueError("Must be either 1 or 0")
        self._old_state = value

    @property
    def new_out_volt(self):
        return self._new_out_volt

    @new_out_volt.setter
    def new_out_volt(self, value):
        self._new_out_volt = value

    @property
    def old_out_volt(self):
        return self._old_out_volt

    @old_out_volt.setter
    def old_out_volt(self, value):
        self._old_out_volt = value

    def get_next_voltage_event(self):
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
