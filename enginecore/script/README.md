## Sim-Engine scripts

This folder contains various scripts used for quite diverse purposes.

`snmppub.lua` is a redis [evalsha](https://redis.io/commands/eval) script that is supplied to `snmpsimd.py` program in its configuration (`.snmprec`) file.

`query_snmp_preset.py` can be used for debugging snmp OIDs managed my simengine (it can read from a preset file).

`db_config.cyp` defines Neo4j database constraints;

`bridges` script can be used to configure virsh network for Anvil! system.

`demo` folder contains various demo scripts used at ARIE showcases for demonstration purposes (for example, rand outlet status toggle for PDU or beat extraction for a music track)

`simengine-run`, `simengine-setup` and `setup` scripts can be used to install & run simengine platform. (these haven't been maintained for quite some time though)
