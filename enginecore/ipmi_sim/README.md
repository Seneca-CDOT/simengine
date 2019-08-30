## IPMI_SIM plugin

`haos_extend.c` is a plugin for `ipmi_sim` that processes IPMI power commands (`ipmitool power on/off` or `ipmitool power status`) by executing simengine commands with `simengine-cli`;

### Compilation

`gcc -shared -o ./haos_extend.so -fPIC ./haos_extend.c`

`sudo mkdir /usr/lib64/simengine`

`sudo cp ./haos_extend.so /usr/lib64/simengine`

### Compile Sensors

Sensor files located in ../ipmi_template are compiled with the `sdrcomp` tool as:

\*.sdrs -> sensor definitions

```
sdrcomp -o main.bsdr main.sdrs

mkdir emu_state/ipmi_sim

mkdir emu_state/ipmi_sim/ipmisim1

cp main.bsdr emu_state/ipmi_sim/ipmisim1/sdr.20.main
```
