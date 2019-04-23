from collections import namedtuple


PowerEventResult = namedtuple(
    "PowerEventResult", "old_state new_state asset_key asset_type"
)
PowerEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)
LoadEventResult = namedtuple(
    "LoadEventResult", "load_change old_load new_load asset_key asset_type"
)
LoadEventResult.__new__.__defaults__ = (None,) * len(PowerEventResult._fields)
