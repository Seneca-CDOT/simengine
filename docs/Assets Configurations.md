# Asset Configurations

## UPS

### SNMP Configurations

You can configure both IP & port of the snmpsim instance:

`simengine-cli model create ups -k=3 --name=an-ups01 --host=192.168.124.3 --port=161`

or

`simengine-cli model update ups -k=3 --name=an-ups01 --host=localhost --port=1024`

!!! note
    Binding to `161` requires `root` access.

### Charge & Drain Speed Factors

`simengine` supports speed-up for both battery recharge and drain.

`simengine-cli configure-state ups -k2 --charge-speed=50`

`simengine-cli configure-state ups -k2 --drain-speed=50`

This factor will be multiplied by the estimated drain/charge percentage per second.

!!! note
    Running this command does not require simengine-core restart.

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

The simengine defaults its SNMP interface settings to APC hardware (outlined here [ups](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_ups.json)). Custom vendor presets can be passed to the `simengine-cli` system modelling tool with the `--snmp-preset=/path/to/my_specs.json` option.

You can find APC examples of .json config files in simengine repo:

- [ups](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_ups.json)
- [pdu](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/apc_pdu.json)

**General Configurations (snmp-preset file description)**

| **JSON property**      | **Description**                                                                                                                                                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| staticOidFile          | `.snmprec` file containing recorded OID tree (see snmpsim doc [reference](http://snmplabs.com/snmpsim/building-simulation-data.html#building-simulation-data)). The simengine will search for the specified file at `SIMENGINE_STATIC_DATA` path |
| assetName              | Name displayed on the UI (can be overwritten with `--name` option)                                                                                                                                                                               |
| numOutlets             | Number of UPS output outlets                                                                                                                                                                                                                     |
| fullRechargeTime       | (hours) Recharge time for a fully depleted battery                                                                                                                                                                                               |
| minPowerOnBatteryLevel | Minimum value of the battery charge before UPS powers up its output                                                                                                                                                                              |
| outputPowerCapacity    | (Watts) UPS output power capacity                                                                                                                                                                                                                |
| modelRuntime           | Runtime graph consisting of key-value pairs `{ wattage: expected runtime in minutes }`More values should yield more accurate results                                                                                                             |

**OID Specifications**

OID JSON structure:

    "OIDName": {
        "OID": "1.3.6....", // Vendor-specific OID
        "dataType": 2, // DataType (e.g. 2-iteger, 67-Timeticks, 66-Gauge etc.)
        "defaultValue": 1, // Value set on engine start
        "oidDesc": { // Value to enum mappings
          "1": "switchOn",
          "2": "switchOff"
        }
    }

| **JSON Property (OID Name)** | **Description**                                                            | **Value Mappings**                     |
| ---------------------------- | -------------------------------------------------------------------------- | -------------------------------------- |
| SerialNumber                 | Asset serial number                                                        |                                        |
| HighPrecBatteryCapacity      | High-precision battery capacity (max 1000)                                 |                                        |
| AdvBatteryCapacity           | Advance battery capacity (max 100%)                                        |                                        |
| BasicBatteryStatus           | Basic status of the UPS battery                                            | batteryNormal, batteryLow              |
| HighPrecOutputLoad           | High-precision load percentage of the total capacity (outputPowerCapacity) |                                        |
| AdvOutputLoad                | load percentage of the total capacity (outputPowerCapacity)                |                                        |
| HighPrecOutputCurrent        | Current UPS load in AMPs (high-precision)                                  |                                        |
| AdvOutputCurrent             | Current UPS load in AMPs                                                   |                                        |
| BatteryRunTimeRemaining      | Run-time left before UPS shuts down                                        |                                        |
| TimeOnBattery                | How long UPS has been running on a battery                                 |                                        |
| PowerOff                     | Power off UPS device                                                       | switchOff,switchOffGraceful            |
| BasicOutputStatus            | Battery status: online, on-battery, offline                                | onLine, onBattery, off                 |
| InputLineFailCause           | Reason behind transferring to the alt. battery power source                | noTransfer, blackout, deepMomentarySag |
| AdvConfigReturnDelay         | Power up delay                                                             |                                        |
| AdvConfigShutoffDelay        | Shut down delay                                                            |                                        |

## Server Type

SimEngine supports 2 types of servers: `server` and `server-bmc`. Asset of type `server` is a simpler variation of `server-bmc` that manages a VM but does not support `IPMI/BMC` or `storcli64` interfaces. Both server types allow up to 2 PSUs at the moment and require power consumption and valid VM domain name specified (`--domain-name={my_vm}` argument).

### BMC Server

Server with IPMI_SIM interface (`server-bmc`) requires specific `.xml` configurations for qemu VM and some manual VM setup for `storcli64`. You can edit `libvirt` config file by issuing this command:

`virsh edit {domain name}`

You will need to change the top-level tag to `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>` and also add `qemu` command line arguments (after `</devices>`).

For instance, this CLI-defined server model:

    simengine-cli model create server-bmc --asset-key=8 \
                                          --domain-name=an-a01n02 \
                                          --power-consumption=360 \
                                          --port=9101 \
                                          --vmport=9102 \
                                          --storcli-port=50001

Will require the following .xml configurations:

    <qemu:commandline>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=ipmi0,host=localhost,port=9102,reconnect=10'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='ipmi-bmc-extern,id=bmc0,chardev=ipmi0'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='isa-ipmi-bt,bmc=bmc0'/>
        <qemu:arg value='-serial'/>
        <qemu:arg value='mon:tcp::9012,server,telnet,nowait'/>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=simengine-storage-tcp,host=localhost,port=50001,reconnect=2'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtio-serial'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtserialport,chardev=simengine-storage-tcp,name=systems.cdot.simengine.storage.net'/>
    </qemu:commandline>

Storage emulation features require `storcli64` executable to be uploaded to the managed vm bin directory.
The binary can be found in simengine repo: [link](https://github.com/Seneca-CDOT/simengine/blob/master/storage-emulation-tests/guest/storcli64)

Here is a breakdown of `server-bmc` command line parameters and some corresponding .xml configurations:

**IPMI Interface**

| Argument   | Description                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------------------- |
| `port`     | IPMI/BMC interface port (used on the host machine): <br> `ipmitool -H localhost -p {port} -U {user}` |
| `user`     | admin user: <br>`ipmitool -H localhost -p {port} -U {user}`                                          |
| `password` | admin user password                                                                                  |

**VM Configurations**

| Argument       | Description                                                                                                                                                                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `vmport`       | Simengine will use this port internally to connect to the VM, <br>this value needs to be configured in libvirt `.xml` definition as: `<qemu:arg value='socket,id=ipmi0,host=localhost,port={vmport},reconnect=10'/>`                                          |
| `storcli-port` | `storcli64` binary will connect to this StorCLI websocket server port on guest OS. <br>The port value needs to be configured in libvirt `.xml` definition as: <br>`<qemu:arg value='socket,id=simengine-storage-tcp,host=localhost,port=50001,reconnect=2'/>` |

**Sensor Model**

SimEngine defaults its IPMI/BMC sensor definitions to the following [model](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/sensors.json). Custom configurations can be passed to the `cli` system modelling tool with the `--sensor-def=/path/to/my_specs.json` option.

Engine supports a limited number of sensor [types](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/supported_sensors.py) and each sensor definition must provide `defaultValue`, `offValue` and `name` as well as `address` if `addressSpace` is not provided. You can also specify any number of thresholds (or none).

    "caseFan": {
        "group": "fan",
        "addressSpace": "0x6f",
        "sensorDefinitions": [
            {
                "thresholds": {
                    "lnr": 0,    // Lower Non-Recoverable
                    "lcr": 200,  // Lower Critical
                    "lnc": 300,  // Lower Non-Critical
                    "unc": 1000, // Upper Non-Critical
                    "ucr": 1200, // Upper Critical
                    "unr": 1500, // Upper Non-Recoverable
                },
                "defaultValue": 0,
                "offValue": 0,
                "name": "Frnt_FAN{index}"
            }
        ]
    }

**Storage Model**

SimEngine uses the following storage topology: [storage.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage.json). Custom configurations can be passed to the `cli` system modelling tool with the `--storage-def=/path/to/my_specs.json` option. You can specify any number of controllers and each controller can include definitions of cache vault (`CacheVault`), virtual and physical drives (`VD` & `PD`).

    {
        // ..storcli64 details
        "controllers": [
            {
                // ..controller 0 details
                "CacheVault": { ... },
                "VD": [
                    {
                        // ..virtual drive 0 details
                        // IDs of the physical drives belonging to the virtual drive
                        "DID": [9, 10, 8]
                    }, { ... }
                ],
                "PD": [
                    { ... },
                    { ... }
                ]
            }, { ... }
        ]
     }

**Storage States**

Storage states file defines how the storage emulator will behave depending on current system states. For example, virtual drive will be set to partially degraded state — `Pdgd` when one of the physical drives is either offline or rebuilding:

    {
        "virtualDrive": {
            "Optl": { ... }
            "Pdgd": {
                "numPdOffline": 1,    // set VD state to Pdgd if true
                "numPdRebuilding": 1, // set VD state to Pdgd if true
                "mediaErrorCount": -1,
                "otherErrorCount": -1,
                "predictiveErrorCount": -1
            },
            "Dgrd": { ... }
        },
        "controller": { ... }
    }

Custom spec file can be passed to the `cli` system modelling tool with the `--storage-states=/path/to/my_specs.json` parameter.
