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
                      [:AssetLoadEvent]┐           [:AssetLoadEvent]┐
                        |              |             |              |
    (Asset#1)<-[:ChildLoadEvent]-(Asset#2)<-[:ChildLoadEvent]-(Asset#3)

    It stops when there are no parent assets or it runs into a UPS with
    absent input power
    """


class BranchTracker:
    """Utility to keep track of power branches in progress/completed"""

    def __init__(self):
        self._branches_active = []
        self._branches_done = []

    @property
    def num_branches_active(self):
        """Number of branches/streams still in progress"""
        return len(self._branches_active)

    @property
    def num_branches_done(self):
        """Number of branches/streams still in progress"""
        return len(self._branches_done)

    @property
    def completed(self):
        """True if all the branches are completed"""
        return self.num_branches_active == 0

    def complete_branch(self, branch: PowerBranch):
        """Remove branch from a list of completed branches"""
        self._branches_active.remove(branch)
        self._branches_done.append(branch)

    def add_branch(self, branch: PowerBranch):
        """Add branch to the collection of tracked branches"""
        self._branches_active.append(branch)

    def extend(self, branches: list):
        """Add many branches to the collection of tracked branches"""
        self._branches_active.extend(branches)


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

        self._volt_branches = BranchTracker()
        self._load_branches = BranchTracker()

        self._last_processed_volt_event = None
        self._last_processed_load_event = None

        self._src_event = src_event
        self._src_event.power_iter = self

    def __str__(self):
        return (
            "Power Iteration due to incoming event:\n"
            " | {0._src_event}\n"
            "Loop Details:\n"
            " | Voltage Branches in-progress: {0._volt_branches.num_branches_active}\n"
            " | Voltage Branches completed: {0._volt_branches.num_branches_done}\n"
            " | Load Branches in-progress: {0._load_branches.num_branches_active}\n"
            " | Load Branches completed: {0._load_branches.num_branches_done}\n"
            " | Last Processed Power Event: \n"
            " | {0._last_processed_volt_event}\n"
            " | Last Processed Load Event: \n"
            " | {0._last_processed_load_event}\n"
        ).format(self)

    @property
    def all_voltage_branches_done(self):
        """Returns true if power iteration has no voltage streams in progress"""
        return self._volt_branches.completed

    @property
    def all_load_branches_done(self):
        """Returns true if power iteration has no load streams in progress"""
        return self._load_branches.completed

    @property
    def power_iteration_done(self):
        """Power iteration is completed when both downstream and upstream
        power event propagation is exhausted"""
        return self.all_load_branches_done and self.all_voltage_branches_done

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

        self._last_processed_volt_event = event

        # asset caused by power loop (individual asset power update)
        if event.kwargs["asset"]:
            return self._process_hardware_asset_event(event)

        # wallpower voltage caused power loop
        return self._process_wallpower_event(event)

    def process_load_event(self, event):
        """Takes asset load event and generates upstream load events
        that will be dispatched against the parent(s);
        Args:
            event(AssetLoadEvent):
        """
        self._last_processed_load_event = event
        parent_keys = self.data_source.get_parent_assets(event.asset.key)
        load_events = None

        if not event.branch:
            self._load_branches.add_branch(LoadBranch(event, self))

        load_events = [event.get_next_load_event()]

        # forked branch -> replace it with 'n' child parent load branches
        if len(parent_keys) > 1:
            new_branches = [
                LoadBranch(event.get_next_load_event(), self) for _ in parent_keys
            ]

            self._load_branches.extend(new_branches)
            load_events = [b.src_event for b in new_branches]

        if not parent_keys or not load_events:
            self._load_branches.complete_branch(event.branch)
            return None

        return zip(parent_keys, load_events)

    def _process_wallpower_event(self, event):
        """Wall-power voltage was updated, retrieve chain events associated
        with mains-powered outlets
        Args:
            event(AssetPowerEvent):
        """
        wp_outlets = self.data_source.get_mains_powered_assets()

        new_branches = [
            VoltageBranch(event.get_next_voltage_event(), self) for _ in wp_outlets
        ]
        self._volt_branches.extend(new_branches)

        return ([(k, b.src_event) for k, b in zip(wp_outlets, new_branches)], None)

    def _process_hardware_asset_event(self, event):
        """One of the hardware assets went online/online
        Args:
            event(AssetPowerEvent): contains asset event results caused 
                                    by input power event (e.g. output voltage
                                    change due to input voltage drop etc.) or
                                    asset getting powered down by the user
        """

        # find neighbouring nodes (parents & children)
        child_keys, parent_keys = self.data_source.get_affected_assets(event.asset.key)

        # no branch assigned to the event yet
        # (e.g. asset was powered down by a user)
        if not event.branch:
            self._volt_branches.add_branch(VoltageBranch(event, self))
            event.set_load()

        # voltage events will be displatched downstream to children of the updated node
        # load events (if any) will be displatched to parents of the updated node
        volt_events = [event.get_next_voltage_event()]
        load_events = None

        if parent_keys and event.get_next_load_event():
            new_branches = [
                LoadBranch(event.get_next_load_event(), self) for _ in parent_keys
            ]
            self._load_branches.extend(new_branches)
            load_events = [b.src_event for b in new_branches]

        # delete voltage branch (power stream) when it forks, when
        #  it reaches leaf asset/node or when voltage hasn't changed
        if (
            (len(child_keys) > 1 and event.branch)
            or not child_keys
            or event.out_volt.unchanged()
        ):
            self._volt_branches.complete_branch(event.branch)

        if event.out_volt.unchanged():
            child_keys = []
        # forked branch -> replace it with 'n' child voltage branches
        elif len(child_keys) > 1:
            new_branches = [
                VoltageBranch(event.get_next_voltage_event(), self) for _ in child_keys
            ]
            self._volt_branches.extend(new_branches)
            volt_events = [b.src_event for b in new_branches]

        return (
            zip(child_keys, volt_events),
            zip(parent_keys, load_events) if load_events else None,
        )
