
# Asset Configurations

## Agents 

You can check if ipmi/snmp simulators are up & running by issuing status command:

`simengine-cli status --asset-key={key} --agent`

## UPS

### SNMP Configurations

You can configure both IP & port of the snmpsim instance:

`simengine-cli model create ups -k=3 --name=an-ups01 --host=192.168.124.3 --port=161`

or 

`simengine-cli model update ups -k=3 --name=an-ups01 --host=localhost --port=1024`

__Note__ : binding to `161` requires `root` access. 

### Charge & Drain Speed Factors

`simengine` supports speed-up for both battery recharge and drain.

`simengine-cli configure-state ups -k2 --charge-speed=50`

`simengine-cli configure-state ups -k2 --drain-speed=50`

This factor will be multiplied by the estimated drain/charge percentage per second.

__Note__ that running this command does not require simengine-core restart.

### Runtime Graph

You can configure UPS runtime chart; For example, `runtime.json` file will map 50 watts to 32 minutes, 100 to 18 min, 200 to 9 min etc.

runtime.json: 

```
{
    "50": 32,
    "100": 18,
    "200": 9,
    "300": 5,
    "400": 3,
    "500": 2
}
```

Updating the model:

`simengine-cli model update ups -k2 --runtime-graph "$(cat ./runtime.json)"`

### Power Capacity

Asset's power capacity can be updated as `simengine-cli model update ups -k2 --power-capacity=1500`

### Full Recharge Time & Min Battery Level

Full recharge time can be configured as following:

`simengine-cli model update ups -k2 --full-recharge-time=1 # set to 1 hour`

The UPS will take 1 hour to recharge a fully depleted battery.

UPS also supports minimum battery level required (before UPS can power up its output outlets):

`simengine-cli model update ups -k2 --min-power-bat=1 # 0.1% required before power is restored`


### Vendor Pre-Set

The simengine defaults its SNMP interface settings to APC hardware (outlined here [ups](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_ups.json)). Custom vendor presets can be passed to the `simengine-cli` system modelling tool with the `--snmp_preset=/path/to/my_specs.json` option. 

You can find APC examples of .json config files in simengine repo:

- [ups](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_ups.json)  
- [pdu](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_pdu.json)


**General Configurations (snmp_preset)**


| **JSON property**      | **Description**                                                                                                                                                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| staticOidFile          | `.snmprec` file containing recorded OID tree (see snmpsim doc [reference](http://snmplabs.com/snmpsim/building-simulation-data.html#building-simulation-data)). The simengine will search for the specified file at `SIMENGINE_STATIC_DATA` path |
| assetName              | Name displayed on the UI (can be overwritten with `--name` option)                                                                                                                                                                              |
| numOutlets             | Number of UPS output outlets                                                                                                                                                                                                                    |
| fullRechargeTime       | (hours) Recharge time for a fully depleted battery                                                                                                                                                                                              |
| minPowerOnBatteryLevel | Minimum value of the battery charge before UPS powers up its output                                                                                                                                                                             |
| outputPowerCapacity    | (Watts) UPS output power capacity                                                                                                                                                                                                               |
| modelRuntime           | Runtime graph consisting of key-value pairs  `{ wattage: expected runtime in minutes }`More values should yield more accurate results                                                                                                          

**OID Specifications**

OID JSON structure:


    "OIDName": {
        "OID": "1.3.6....", // Vendor-specific OID
        "dataType": 2, // DataType (e.g. 2-iteger, 67-Timeticks, 66-Gauge etc.)
        "defaultValue": 1, // Value set on engine start
        "oidDesc": { // Value to enum mappings
          "`1`": "switchOn",
          "`2`": "switchOff"
        }
    }


| **JSON Property (OID Name)** | **Description**                                                            | **Value Mappings**                   |
| ---------------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
| SerialNumber                 | Asset serial number                                                        |                                      |
| HighPrecBatteryCapacity      | High-precision battery capacity (max 1000)                                 |                                      |
| AdvBatteryCapacity           | Advance battery capacity (max 100%)                                        |                                      |
| BasicBatteryStatus           | Basic status of the UPS battery                                            | batteryNormal, batteryLow             |
| HighPrecOutputLoad           | High-precision load percentage of the total capacity (outputPowerCapacity) |                                      |
| AdvOutputLoad                | load percentage of the total capacity (outputPowerCapacity)                |                                      |
| HighPrecOutputCurrent        | Current UPS load in AMPs (high-precision)                                  |                                      |
| AdvOutputCurrent             | Current UPS load in AMPs                                                   |                                      |
| BatteryRunTimeRemaining      | Run-time left before UPS shuts down                                        |                                      |
| TimeOnBattery                | How long UPS has been running on a battery                                 |                                      |
| PowerOff                     | Power off UPS device                                                       | switchOff,switchOffGraceful          |
| BasicOutputStatus            | Battery status: online, on-battery, offline                                | onLine, onBattery, off               |
| InputLineFailCause           | Reason behind transferring to the alt. battery power source                | noTransfer, blackout, deepMomentarySag |
| AdvConfigReturnDelay         | Power up delay                                                             |                                      |
| AdvConfigShutoffDelay        | Shut down delay                                                            |                                      |

## Server Type

Server asset can manage VMs state and control its power. It supports up to 2 PSUs at the moment and requires power consumption and valid VM domain name specified (`--domain-name={my_vm}` argument).

Server with IPMI_SIM interface (`server-bmc`) requires specific `.xml` configurations for qemu VM. You can edit `libvirt` config file 
by issuing this command:

`virsh edit {domain name}`

You will need to change the top-level tag to `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>` and also add `qemu` command line arguments (after `</devices>`) as following:


    <qemu:commandline>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=ipmi0,host=localhost,port=9002,reconnect=10'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='ipmi-bmc-extern,id=bmc0,chardev=ipmi0'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='isa-ipmi-bt,bmc=bmc0'/>
        <qemu:arg value='-serial'/>
        <qemu:arg value='mon:tcp::9012,server,telnet,nowait'/>
    </qemu:commandline>



Here's a sample model consisting of 2 outlets, 1 PDU, microwave and a server (controlling a VM named `fedora27`):

    # Create 2 outlets, one powers PDU another one powers PSU2
    simengine-cli model create outlet --asset-key=1
    simengine-cli model create outlet --asset-key=2

    # Add a PDU 
    simengine-cli model create pdu --asset-key=3 --port=1024
   
    # Add one useless microwave
    simengine-cli model create static --asset-key=4 --name='Panasonic' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=120

    # Add server that supports BMC & IPMI
    simengine-cli model create server-bmc -k=5 --domain-name=fedora27 --power-consumption=480 --psu-num=2 --psu-load 0.5 0.5

    # Power up the components
    simengine-cli model power-link --source-key=1 --dest-key=3
    simengine-cli model power-link --source-key=31 --dest-key=4
    simengine-cli model power-link --source-key=35 --dest-key=51
    simengine-cli model power-link --source-key=2 --dest-key=52


The IPMI interface can be queried as:

`ipmitool -H localhost -p 9001 -U ipmiusr -P test sdr list`

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power status`

SNMP interface can be queried as:

`snmpget -c public -v 1 127.0.0.1:1024  1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.3`

`snmpwalk -c public -v 1 127.0.0.1:1024`

