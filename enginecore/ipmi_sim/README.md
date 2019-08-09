
### Compile Sensors

*.sdrs -> sensor definitions

```
sdrcomp -o main.bsdr main.sdrs

mkdir emu_state/ipmi_sim

mkdir emu_state/ipmi_sim/ipmisim1

cp main.bsdr emu_state/ipmi_sim/ipmisim1/sdr.20.main
```


### ipmi_sim_extend

`gcc -shared -o ./haos_extend.so -fPIC ./haos_extend.c`

`sudo mkdir /usr/lib64/simengine`

`sudo cp ./haos_extend.so  /usr/lib64/simengine`
