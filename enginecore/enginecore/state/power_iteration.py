"""Tools for keeping track of the ongoing donwtream & upstream power event flow"""
import logging


class PowerBranch:
    """A graph path representing power-event flow"""

    def __init__(self, src_event, power_iter):
        self._src_event = src_event
        self._src_event.branch = self
        self._power_iter = power_iter

    @property
    def src_event(self):
        """Get root node/root access of the branch (one that started it all)"""
        return self._src_event

    def __call__(self):
        return self.src_event


class VoltageBranch(PowerBranch):
    """Voltage Branch represents a graph path of chained voltage
    events propagated downstream:
    [:AssetVoltageEvent]┐           [:AssetVoltageEvent]┐
         |              |                |              |
    (Asset#1)-[:InputVoltageEvent]->(Asset#2)-[:InputVoltageEvent]->(Asset#3)

    It stops when child nodes are exhausted or voltage event propogation is stopped
    (e.g. when it encounters a UPS)
    """


class LoadBranch(PowerBranch):
    """Voltage Branch represents a graph path of chained load events
    propagated upstream:
                      [:AssetLoadEvent]┐              [:AssetLoadEvent]┐
                        |              |                |              |
    (Asset#1)<-[:InputVoltageEvent]-(Asset#2)<-[:InputVoltageEvent]-(Asset#3)

    It stops when there are no parent assets or it runs into a UPS with
    absent input power
    """


class PowerIteration:
    """Power Iteration is initialized when a new incoming voltage event is
    detected (either due to some asset being powered down or wallpower 
    blackout/restoration).

    It consists of voltage events dispatched downstream (voltage branching)
    and load events upstream (load branching).
    Power iteration completes when all of the voltage and load branches are processed.
    """

    data_source = None

    def __init__(self, src_event):
        """Source """
        self._volt_branches_active = []
        self._volt_branches_done = []

        self._load_branches_active = []
        self._load_branches_done = []

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
            " | Number Load Branches in-progress: {0.num_load_branches_active}\n"
            " | Number Load Branches completed: {0.num_load_branches_done}\n"
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

    @property
    def num_load_branches_active(self):
        """Number of load branches/streams still in progress"""
        return len(self._load_branches_active)

    @property
    def num_load_branches_done(self):
        """Number of load branches/streams still in progress"""
        return len(self._load_branches_done)

    def complete_volt_branch(self, branch: VoltageBranch):
        """Remove branch from a list of completed branches"""
        self._volt_branches_active.remove(branch)
        self._volt_branches_done.append(branch)

    def complete_load_branch(self, branch: LoadBranch):
        """Remove branch from a list of completed branches"""
        self._load_branches_active.remove(branch)
        self._load_branches_done.append(branch)

    def launch(self):
        """Start up power iteration by returning events
        Returns:
            tuple consisting of:
                - ParentAssetVoltageEvent (either up or down)
                - ChildLoadEvent     (either up or down)
        """
        return self.process_power_event(self._src_event)

    def process_power_event(self, event):
        """Retrieves events as a reaction to the passed source event
        Args:
            event(AssetPowerEvent):
        """

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
        Args:
            event(AssetPowerEvent):
        """
        wp_outlets = self.data_source.get_mains_powered_assets()

        new_branches = [VoltageBranch(event, self) for _ in wp_outlets]
        self._volt_branches_active.extend(new_branches)

        return (
            [
                (k, b.src_event.get_next_voltage_event())
                for k, b in zip(wp_outlets, new_branches)
            ],
            None,
        )

    def _process_hardware_asset_event(self, event):
        """One of the hardware assets went online/online
        Args:
            event(AssetPowerEvent):
        """

        from pprint import pprint as pp

        pp(event)
        pp(event.kwargs["asset"])
        child_keys, parent_keys = self.data_source.get_affected_assets(event.asset.key)

        if not event.branch:
            self._volt_branches_active.append(VoltageBranch(event, self))

        events = [event.get_next_voltage_event()]

        # forked branch -> replace it with 'n' child voltage branches
        if len(child_keys) > 1:
            new_branches = [
                VoltageBranch(event.get_next_voltage_event(), self) for _ in child_keys
            ]
            self._volt_branches_active.extend(new_branches)
            events = [b.src_event for b in new_branches]

        # delete voltage branch (power stream) when it forks
        # or when it reaches leaf asset/node
        if (len(child_keys) > 1 and event.branch) or not child_keys:
            self.complete_volt_branch(event.branch)

        return (zip(child_keys, events), None)
