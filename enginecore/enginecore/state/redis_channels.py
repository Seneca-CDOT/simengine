"""Pub/Sub redis channels details """

class RedisChannels():
    """Load, state & oid update channels 
    
    - load is fired every time asset's load is updated
    - state is only fired when notification is enabled on asset's state manager
    - oid udpate is fired every time SET command is issued agains an oid (done by SNMPsim, see 'scripts/snmppub.lua')
    """
    load_update_channel = 'load-upd'
    state_update_channel = 'state-upd'
    oid_update_channel = 'oid-upd'
    battery_update_channel = 'battery-upd'
