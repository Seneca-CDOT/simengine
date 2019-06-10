"""Aggregates Assets' responses to certain events
For example, PowerEventResult will be returned to the dispatcher
in case the dispatched event was handled succesfully
"""

from collections import namedtuple

PowerEventResult = namedtuple(
    "PowerEventResult", "old_state new_state load_change asset_key asset_type"
)
PowerEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)

LoadEventResult = namedtuple(
    "LoadEventResult", "old_load new_load asset_key asset_type parent_key"
)
LoadEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)

VoltageEventResult = namedtuple(
    "VoltageEventResult", "old_voltage new_voltage asset_key asset_type"
)
VoltageEventResult.__new__.__defaults__ = (None,) * len(VoltageEventResult._fields)
