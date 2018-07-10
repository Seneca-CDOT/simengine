`sudo dnf install hiredis-devel`


### Compile Sensors

*.sdrs -> sensor definitions

```
sdrcomp -o main.bsdr main.sdrs

mkdir emu_state/ipmi_sim

mkdir emu_state/ipmi_sim/ipmisim1

cp main.bsdr emu_state/ipmi_sim/ipmisim1/sdr.20.main
```


### ipmi_sim_extend

`sudo dnf install -y hiredis-devel`

` gcc -shared -o ./haos_extend.so -fPIC ./haos_extend.c -lhiredis`

### Running Simulator

`ipmi_sim -c ./lan.conf -f ipmisim1.emu -s emu_state`