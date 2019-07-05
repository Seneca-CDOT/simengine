from circuits import Component, Event, Worker, Debugger, handler


class PowerEvent(Event):
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
    success = True

    def get_next_voltage_event(self, source_e_result):

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
