"""Pub/Sub redis channels details """


class RedisChannels:
    """Load, state & oid update channels

    - load is fired every time asset's load is updated
    - state is only fired when notification is enabled on asset's state manager
    - mains update is fired when wall power becomes unavailable
    - oid udpate is fired every time SET command is issued agains an oid
                    (done by SNMPsim by executing evalsha in 'scripts/snmppub.lua')
    - model update is fired upon asset topology changes
    """

    # power
    load_update_channel = "load-upd"
    state_update_channel = "state-upd"
    mains_update_channel = "mains-upd"
    voltage_update_channel = "voltage-upd"

    # battery states
    battery_update_channel = "battery-upd"
    battery_conf_drain_channel = "battery-drain-upd"
    battery_conf_charge_channel = "battery-charge-upd"

    # thermal channels
    ambient_update_channel = "ambient-upd"
    sensor_conf_th_channel = "sensor-th-upd"
    cpu_usg_conf_th_channel = "cpu-th-upd"
    str_drive_conf_th_channel = "drive-th-upd"
    str_cv_conf_th_channel = "cv-th-upd"

    # misc
    oid_update_channel = "oid-upd"
    model_update_channel = "model-upd"
