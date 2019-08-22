## Data

### SNMP data

`pdu` & `ups` folders contain SNMP vendor mibs as well as .snmprec recordings from real APC devices collected with `snmprec.py` [tool](http://snmplabs.com/snmpsim/documentation/recording-with-variation-modules.html):

```bash
$ snmprec.py --agent-udpv4-endpoint={device-url}  \
                    --start-oid=1.3.6   \
                    --output-file==public.snmprec
```

The .snmprec files are data sources for `simengine` SNMP simulators & are used to populate SNMP object tree in  `redis`.

### Virsh Configurations

`virsh` folder contains .xml dumps for alteeve's VMs which can be easily imported for [Anvil modelling](https://simengine.readthedocs.io/en/latest/Anvil%20Model/). 

### SDR Sensor Readings

`real-sensor-readings` folder contains real IPMI sensor values recorded under okay & stress conditions, such as:

- everything is fine: [sdr_ok.txt](./real-sensor-readings/sdr_ok.txt)
- AC loss for PSU2: [sdr_no_ac_to_psu.txt](./real-sensor-readings/sdr_no_ac_to_psu.txt)
- server is offline: [sdr_server_off.txt](./real-sensor-readings/sdr_server_off.txt)
