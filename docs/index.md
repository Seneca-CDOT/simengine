# Sim Engine


Simengine is a hardware simulation engine that can model Alteeve's Anvil! Intelligent Availability platform and similar high-availability setups.

The engine can reconstruct behaviour of system’s core components such as PDUs, UPSes & servers (running the VMs). PDUs support SNMP interface and servers can be set up with an optional IPMI simulator.  

The project exposes core assets’ functionalities through both GUI and UI though limited to the power component at the moment. Some management tools can be utilised through the Redis `pub/sub` based communication as well.

You can model your own set-up (see [System Modelling](./SystemModeling.md)) and automate/perform power-related tasks (see [Power Management](./PowerManagement.md)).


![](./server.png)

