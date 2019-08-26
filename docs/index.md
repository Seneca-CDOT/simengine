# Sim Engine

SimEngine is a hardware simulation engine that can model [Alteeve’s](https://www.alteeve.com/c/) Anvil! Intelligent Availability platform and similar high-availability setups.

The engine can reconstruct behaviour of system’s core components such as PDUs, UPSes & servers (running the VMs). PDUs and UPSes support SNMP interface, server-type assets can be set up with an optional IPMI simulator and/or storcli64 simulator.

The project exposes core assets’ functionalities through both CLI and UI, although dashboard utilizes only a limited set of power-related features at the moment.

SimEngine features include:

- System modelling & power connections (PDU, UPS, Servers & VM control)
- Power events (wallpower, assets' states, UPS battery etc)
- IPMI/BMC interface and SNMP simulation (including load & power behaviour)
- Thermal simulation (AC & Ambient, temperature sensors)
- storcli64 simulation (Drive/CacheVault failure, temperature behaviour etc.)

### Getting Started

[Installation](./Installation) page provides a guide for the platform set-up. You can model your own hardware topology (see [System Modelling](./System%20Modeling)) or check a real-world high-availability system example (see [Anvil Model](./Anvil%20Model));

### Developing for SimEngine

[Installation](./Installation/#development-version) page includes steps on how to run this app in a development mode. SimEngine is pretty much restricted to CentOS-based platforms (it is suggested you use the latest Fedora systems as we test/develop on Fedora), however, it should run just as fine on any other linux-based OS.

Make sure you read our [contributing guidelines](https://github.com/Seneca-CDOT/simengine/blob/master/CONTRIBUTING.md) before proposing some exciting changes!


![](./server.png)
