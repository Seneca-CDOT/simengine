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

Some server parts can have thermal impact on others e.g.,  a case fan will be cooling its neighbouring server components (CPU, memory etc.) whereas a working PSU may cause the opposite effect.

![](./ThermalSensors.png)

You can query all thermal relationships for a particular server:

`simengine-cli thermal sensor get --asset-key=5`

Or select a specific sensor:

`simengine-cli thermal sensor get --asset-key=5 --sensor='Frnt_FAN2``'`


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

Note : most thermal cases require both ‘up’ and ‘down’ events configured
(‘Frnt_FAN2’ going down should result in temperature spikes for Memory slot(s)). 

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

