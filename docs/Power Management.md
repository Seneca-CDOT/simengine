# Power Management

Power can be managed though either UI or `simengine-cli`, for example:

### ON

`simengine-cli power on -k1` 

will power asset under key `1`.

### OFF

You can power asset off with `power down` command:

`simengine-cli power down -k1` 


### Status

You can get assets' status with `simengine-cli status` (this will also dislay load).

### UI

UI presents a toggle option that can change asset's status to either on or off. Click on any component and check the `Toggle Status` to update the state.

### IPMI-enabled Server

You can also use `ipmitool` to communicate commands to the ipmi simulator instance:

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power status`

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power off`

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power on`

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power cycle`

