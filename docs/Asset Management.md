## Agents

You can check if ipmi/snmp simulators are up & running by issuing status command:

`simengine-cli status --asset-key={key} --agent`

## Power Management

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

### Wall Power

Wall power affects outlets' power & thermal state of the environment. It can be queried with:

`simengine-cli status --mains`

You can control the mains with the following commands:

`simengine-cli power outage`

`simengine-cli power restore`

Running this will power down all the electrical outlets and switch off AC.

## Thermal Simulation

Simengine can emulate thermal conditions such as room temperature & AC, internal server heating/cooling behaviour. ‘Out-of-the-box’ system will be defaulted to a rather limited state so some advance thermal operations (e.g. sensor interrelationship) will need to be configured by the simengine user.

### Ambient

Ambient is affected by the virtual AC configurations and can rise/fall depending on the wall power state.

Ambient (room temperature) can be queried as:

`simengine-cli thermal ambient get`

This command will report current room temperature value as well as the AC settings:

    Ambient: 21.0°
    AC settings:
     -> [online]  : decrease by 1°/20 sec, until 21° is reached
     -> [offline] : increase by 1°/20 sec, until 28° is reached

The last 2 lines summarize ambient behaviour upon AC state changes where, for instance, working AC (`[online]`) should cool down virtual system environment by 1° every 20 seconds until 21° degrees is reached.

You can set ambient to 28° (note that AC will start cooling down the system immediately according to the configurations):

`simengine-cli thermal ambient set --degrees=28`

Or change AC behaviour (on AC going offline in this case):

`simengine-cli thermal ambient set --rate=2 --degrees=1 --pause-at=28 --event=down`

AC is affected by the mains state (power outage or restoration), for instance, running this command should result in room temperature rising:

`simengine-cli power outage`

### Sensor Interrelationship

Some server parts can have thermal impact on others e.g., a case fan will be cooling its neighbouring server components (CPU, memory etc.) whereas a working PSU may cause the opposite effect.

![](./ThermalSensors.png)

You can query all thermal relationships for a particular server:

`simengine-cli thermal sensor get --asset-key=5`

Or select a specific sensor:

`simengine-cli thermal sensor get --asset-key=5 --sensor='Frnt_FAN2'`

### Configuring Interrelationships

The command-line interface exposes tools for modelling thermal relationships between server parts. You can configure one connection at a time and provide source (sensor causing thermal impact) and target (affected sensor) names as well as event and action details. Event is used to determine when to trigger or enable thermal action (e.g. on source event going ‘offline’) and action indicates whether target sensor value should be increased or decreased.

For example, this CLI command:

    simengine-cli thermal sensor set \
            --asset-key=5 \
            --source-sensor='Frnt_FAN2' \
            --target-sensor='Mem E' \
            --event=up \
            --action=decrease \
            --rate=5 \
            --degrees=1 \
            --pause-at=21

will set ‘Frnt_FAN2’ to cool down ‘Mem E’ temperature every 5 seconds by 1°.

!!! note
    Most thermal cases require both ‘up’ and ‘down’ events configured (‘Frnt_FAN2’ going down should result in temperature spikes for Memory slot(s)).

Second thermal option - increase memory temperature when fan is not operating:

    simengine-cli thermal sensor set \
          --asset-key=5 \
          --source-sensor='Frnt_FAN2' \
          --target-sensor='Mem E' \
          --event=down \
          --action=increase \
          --rate=5 \
          --degrees=1 \
          --pause-at=39

This thermal behaviour can be tested by setting RPM value of a Fan#2 to 0:

`simengine-cli configure-state sensor -k5 -s'Frnt_FAN2' -r0`

Sensor relationships outlined above can be deleted with the following commands:

```bash
simengine-cli thermal sensor delete -s'Frnt_FAN2' -t'Mem E' -e=down -k5
simengine-cli thermal sensor delete -s'Frnt_FAN2' -t'Mem E' -e=up -k5
```

### Model-Based Relationship

The configuration outlined in the previous section results in a binary behaviour where the source sensor is either on or off (any positive value/0). Simengine supports a model-based thermal configuration that requires a JSON formatted source-target mappings.

model.json (RPM value mapped to degrees):

    {
      "400": 1,
      "600": 2,
      "1200": 3
    }

Configure thermal relationship using the model:

     simengine-cli thermal sensor set \
        --asset-key=5 \
        --source-sensor='Frnt_FAN1' \
        --target-sensor='Mem E'\
        --action=decrease \
        --rate=3 \
        --pause-at=21 \
        --model="$(cat ./model.json)"

### Sensors and CPU Usage

It is also possible to set a relationship between cpu load of the virtual machine SimEngine is running and certain IPMI sensors (e.g. `CPU Temperature`):

    simengine-cli thermal cpu-usage set \
      --target-sensor='CPU2 temperature' \
      --model='{"10": 1, "20": 4, "80": 5}' \
      --asset-key=5

The ‘model’ consists of mappings of cpu load to thermal impact e.g., at cpu load 10%, 1° will be added 'CPU2 temperature’.

You can query cpu load configurations with:

`simengine-cli thermal cpu-usage get --asset-key=5`

    Server [5]:
     --> t:[CPU1 temperature] using model '{"10": 1, "20": 4, "80": 10}'

### Sensors and Storage Components

SimEngine's `storcli64` emulator outputs temperature readings associated with CacheVault and physical drives. Sensor/hard drive components’ interrelationships can be configured similar to sensor/sensor interrelationships.

For instance, this command creates a thermal connection between cache vault (under serial number 17703) and `PSU1 Power` bmc sensor:

    simengine-cli thermal storage set \
      --asset-key=5 \
      --source-sensor='PSU1 power' \
      --event=up \
      --action=increase \
      --rate=1 \
      --degrees=1 \
      --pause-at=28 \
      --controller=0 \
      --cache-vault=17703

    simengine-cli thermal storage set \
      --asset-key=5 \
      --source-sensor='PSU1 power' \
      --event=down \
      --action=decrease \
      --rate=1 \
      --degrees=1 \
      --pause-at=28 \
      --controller=0 \
      --cache-vault=17703

You can also make bmc sensor ‘target’ a physical drive. The following configuration will make a physical drive 9 cool down when upstream power is not present (PSU2 is offline).

    simengine-cli thermal storage set \
      --asset-key=5 \
      --source-sensor='PSU2 power' \
      --event=up \
      --action=increase \
      --rate=1 \
      --degrees=1 \
      --pause-at=28 \
      --controller=0 \
      --drive=9

    simengine-cli thermal storage set \
      --asset-key=5 \
      --source-sensor='PSU2 power' \
      --event=down \
      --action=decrease \
      --rate=1 \
      --degrees=1 \
      --pause-at=28 \
      --controller=0 \
      --drive=9

## Storage Simulation

SimEngine supports a built-in `storcli64` simulator that can reconstruct core storage behaviour. The Storage Command Line Tool (StorCLI) is the command line management software designed for the MegaRAID® product line. SimEngine’s `storcli64` simulator accepts query(read)-only cli commands limited to [alteeve’s](https://www.alteeve.com/c/) Anvil! platform requirements at the moment.

**Commands**

| **storcli64 command**                | **Details**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `storcli64 /c0 show perfmode`        | Show performance mode                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `storcli64 /c0 show bgirate`         | Background Initialization (BGI) is an automated process that writes the parity or mirrors data on newly created virtual disks.<br><br>Defined at the model creation in [storage.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage.json) as “bgiRate”                                                                                                                                                                                                                                                                                    |
| `storcli64 /c0 show ccrate`          | The CC (Check Consistency) Rate determines the rate at which consistency check scans are performed on a disk to determine if data is corrupted. <br><br>Defined at the model creation in [storage.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage.json) as “ccRate”                                                                                                                                                                                                                                                                   |
| `storcli64 /c0 show rebuildrate`     | Hard drive rebuild rate for a RAID Controller<br><br>Defined at the model creation in [storage.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage.json) as “ccRate”                                                                                                                                                                                                                                                                                                                                                                      |
| `storcli64 /c0 show prrate`          | Patrol Read Rate for a RAID Controller<br><br>Defined at the model creation in [storage.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage.json) as “prRate”                                                                                                                                                                                                                                                                                                                                                                             |
| `storcli64 /c0 show alarm`           | Display alarm state for a RAID Controller<br><br>Can be set to either `on/off/missing` with:<br>`simengine-cli storage controller set --asset-key=5 --controller=0 --alarm-state=on`                                                                                                                                                                                                                                                                                                                                                                                                         |
| `storcli64 /c0 show all`             | A RAID controller is a hardware device or software program used to manage hard disk drives in a computer or storage array.<br><br>Some controller-associated properties, such as `Memory Correctable Errors` and `Memory Uncorrectable Errors` can be set with `simengine-cli`<br><br>see `simengine-cli storage controller set -h` for more details.                                                                                                                                                                                                                                        |
| `storcli64 /c0 /bbu show all`        | Show BBU details (Backup Battery Unit supporting cache for up to 72 hours until a machine is brought back on line)                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `storcli64 /c0 /cv show all`         | Display cache vault (flash-based cache protection).<br><br>Replacement status can be updated with: <br>`simengine-cli storage cv set --asset-key=5 --controller=0 --replacement-required="Yes"`<br><br>Sometimes cache vault fails to change its mode to `WriteThrough` (this may result in data loss):<br>`simengine-cli storage cv set --asset-key=5 --controller=0 --write-through-fail`                                                                                                                                                                                                  |
| `storcli64 /c0 /vall show all`       | Display virtual drives<br><br>Virtual drive states will change depending on [storage_state.json](https://github.com/Seneca-CDOT/simengine/blob/master/enginecore/enginecore/model/presets/storage_states.json) definition file and current status of physical drives or other storage components.<br><br>For example with out-of-the-box settings, virtual drive state will be set to `Pdgd` (partially degraded) if one of the physical drives belonging to the virtual space is set offline:<br><br>`simengine-cli storage pd set --asset-key=5 --controller=0 --drive-id=7 --state=Offln` |
| `storcli64 /c0 /eall /sall show all` | Display physical drives<br><br>Error counts, such as `Media Error Count`, `Other Error Count` and `Predictive Error Count` are settable (see `simengine-cli storage pd set -h`)<br><br>Drive state can be set to either `Onln` or `Offln`:<br>`simengine-cli storage pd set --asset-key=5 --controller=0 --drive-id=7 --state=Offln`                                                                                                                                                                                                                                                         |

## Playback Scenarios

You can register your own scripts with `simengine-cli` and execute them through either `cli` or SimEngine dashboard:

    # Provide a folder SimEngine would register scripts from
    simengine-cli play folder --path='~/dev/plays'
    ls ~/dev/plays
          outlet_test.sh   # bash (simengine-cli)
          pdu_test.py      # using python api

    # execute a script
    simengine-cli play execute outlet_test

## Action Recorder

SimEngine recorder captures actions performed by the user and offers replay functionalities.

For example, actions such as PDU power down get recorded and users can replay all or a specific range of actions.

Recorder itself can register and replay the following actions:

- asset power control (shut down/power off/power up)
- wall-power control (power outage/power restore)
- ambient control (when set by the user)
- configure sensor (when set by the user)
- physical drives (record media, predictive & other error counts as well as state)
- cache-vault (replacement required)
- controller (alarm state, memory errors)

**Query Actions**

You can list recorded actions with `simengine-cli actions list` as in this example:

```bash
$ simengine-cli power down -k61 # record one
$ simengine-cli power up -k61   # record two
$ simengine-cli actions list # query action history
0) [2019-04-02 10:39:31] IStaticDeviceManager(61).shut_down()
1) [2019-04-02 10:39:37] IStaticDeviceManager(61).power_up()
```

**Dry Run**

Dry run command will display actions to be performed without actually executing them, this can be useful for some forms of debugging:

```bash
$ simengine-cli actions dry-run
0) [executing]: IStaticDeviceManager(61).shut_down()
    [sleeping]:  6 seconds
    .
    .
    .
    .
    .
    .
1) [executing]: IStaticDeviceManager(61).power_up()
```

**Saving Actions**

Note that action history is stored in memory so all the records will be lost upon `enginecore` service restart. Alternatively, you can save action history with

`simengine-cli actions save --filename=my_action_history.json`

and load actions from JSON file later on:

`simengine-cli actions load --filename=my_action_history.json`

When you load action history from a file, any actions stored in the recorder will be deleted/overwritten.

**Deleting Actions**

Actions can be deleted upon a request with `simengine-cli actions clear`, you can also delete a slice of actions with `--start` & `--end` range specifiers.

**Replay**

Replay CLI command will make SimEngine execute previously recorded actions. For instance, if you power down 3 static assets and power them back up, you action history will look like:

```bash
0) [2019-04-02 11:06:21] IStaticDeviceManager(61).shut_down()
1) [2019-04-02 11:06:22] IStaticDeviceManager(62).shut_down()
2) [2019-04-02 11:06:24] IStaticDeviceManager(63).shut_down()
3) [2019-04-02 11:06:25] IStaticDeviceManager(61).power_up()
4) [2019-04-02 11:06:27] IStaticDeviceManager(62).power_up()
5) [2019-04-02 11:06:29] IStaticDeviceManager(63).power_up()
```

You can replay all actions by issuing `simengine-cli actions replay` (this will result in execution of the power-cycle outlined above).

Alternatively, you can replay only a certain range of actions;

Perform only steps number 2 and 3:

```bash
$ simengine-cli actions replay --list --start=2 --end=4
2) [2019-04-02 11:06:24] IStaticDeviceManager(63).shut_down()
3) [2019-04-02 11:06:25] IStaticDeviceManager(61).power_up()
```

Replay only the last recorded action:

```bash
$ simengine-cli actions replay --list --start=-1
5) [2019-04-02 11:06:29] IStaticDeviceManager(63).power_up()
```

Replay actions that occured today between "11:06:22" and "11:06:27"

```bash
$ simengine-cli actions replay --list --start="11:06:22" --end="11:06:27"
1) [2019-04-02 11:06:22] IStaticDeviceManager(62).shut_down()
2) [2019-04-02 11:06:24] IStaticDeviceManager(63).shut_down()
3) [2019-04-02 11:06:25] IStaticDeviceManager(61).power_up()
4) [2019-04-02 11:06:27] IStaticDeviceManager(62).power_up()
```


**Recorder Status**

Recorder can be disabled with `simengine-cli actions disable` & enabled back with `simengine-cli actions enable`.

When disabled, recorder ignores any incoming commands. The status itself can be queried with:

```bash
  $ simengine-cli actions status
  Enabled: True    # - is recorder capturing new actions?
  Replaying: False # - is recorder replaying any commands?
```

## Action Randomizer

SimEngine can spawn random actions associated with the components belonging to your system topology.

Generated events are recorded just like any other actions executed through SimEngine interface and can be later replayed/saved (see [Action Recorder](./Asset%20Management/#action-recorder)).

```bash
$ simengine-cli actions random # generate one random action, pick random asset
$ simengine-cli actions list   # view action history
0) [2019-04-11 10:57:35] IOutletStateManager(44).shut_down()
```

Randomizer can generate any of the [recordable](./Asset%20Management/#action-recorder) actions although some events are limited in regards to the possible randomised parameters. For instance, only fan sensor get their values randomly generated and only if they support sensor thresholds.

`actions random` command can either generate a certain number of random events with `--count` parameter or execute random actions for a specific time-period (`--seconds` argument).

Pauses between actions can have a fixed value supplied with `--nap-time` or you can also provide min and max sleep time with both `--min-nap` & `--nap-time` (max) arguments.

For example, the following command will generate 4 random actions associated with asset#5. The nap time between each action will be randomly assigned a value between 1 and 4.

```bash
$ simengine-cli actions random --count=4       # num of random actions \
                                --min-nap=1    # min pause \
                                --nap-time=4   # max possible pause time \
                                --asset-keys 5 # only inlcude asset under id 5
```

Result:

```bash
0) [2019-04-11 11:12:37] IBMCServerStateManager(5).set_controller_prop(0, {'alarm': 'on'})
1) [2019-04-11 11:12:38] IBMCServerStateManager(5).power_off()
2) [2019-04-11 11:12:41] IBMCServerStateManager(5).set_cv_replacement(0, 'No', True)
3) [2019-04-11 11:12:43] IBMCServerStateManager(5).power_up()
```

**Tweaking Random Ranges**

Some numeric values, such as ambient and controller/disk errors, are always generated within a certain range.

Querying default numeric range parameters for random generator:

```bash
$ simengine-cli configure-state randomizer  --list --asset-key=5
Ambient random arguments: range from 19 to 28
Server:[5] random arguments:
  -- pd-media-error-count: range from 0 to 10
  -- pd-other-error-count: range from 0 to 10
  -- pd-predictive-error-count: range from 0 to 10
  -- ctrl-memory-correctable-errors: range from 0 to 10
  -- ctrl-memory-uncorrectable-errors: range from 0 to 10
```

You can tweak these parameters by providing option to be updated, start and end range specifiers (in this case, memory correctable errors for a controller will be within 33 to 80 numeric range):

```bash
$ simengine-cli configure-state randomizer --option=ctrl-memory-correctable-errors \
                                          --start=33 \
                                          --end=80 \
                                          --asset-key=5 # optional for ambient
```