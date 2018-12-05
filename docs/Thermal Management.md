
# Thermal Simulation

Simengine can emulate thermal conditions such as room temperature & AC, internal server heating/cooling behaviour. ‘Out-of-the-box’ system will be defaulted to a rather limited state so some advance thermal operations (e.g. sensor interrelationship) will need to be configured by the simengine user.


## Ambient

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


##  IPMI/BMC Sensors

**Sensor Interrelationship**

Some server parts can have thermal impact on others e.g.,  a case fan will be cooling its neighbouring server components (CPU, memory etc.) whereas a working PSU may cause the opposite effect.

![](./ThermalSensors.png)

You can query all thermal relationships for a particular server:

`simengine-cli thermal sensor get --asset-key=5`

Or select a specific sensor:

`simengine-cli thermal sensor get --asset-key=5 --sensor='Frnt_FAN2``'`


**Sensors and CPU Usage**

It is also possible to set a relationship between cpu load of the virtual machine SimEngine is running and certain IPMI sensors (e.g. `CPU Temperature`):


    simengine-cli thermal cpu-usage set \
      --target-sensor='CPU2 temperature' \
      --model='{"10": 1, "20": 4, "80": 5}' \
      --asset-key=5

