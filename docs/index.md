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

![Sample Model of Digital Infrastructure](./server.png)

### Getting Started

[Installation](./Installation) page provides a guide for the platform set-up. You can model your own hardware topology (see [System Modelling](./System%20Modeling)) or check a real-world high-availability system example (see [Anvil Model](./Anvil%20Model));

### Developing for SimEngine

[Installation](./Installation/#development-version) page includes steps on how to run this app in a development mode. SimEngine is pretty much restricted to CentOS-based platforms (it is suggested you use the latest Fedora systems as we test/develop on Fedora), however, it should run just as fine on any other linux-based OS.

Make sure you read our [contributing guidelines](https://github.com/Seneca-CDOT/simengine/blob/master/CONTRIBUTING.md) before proposing some exciting changes!

## Project Overview

SimEngine was designed to reconstruct Alteeve's digital infrastructure [Anvil!](https://www.alteeve.com/w/What_is_an_Anvil!_and_why_do_I_care%3F) and simulate common hardware scenarios such as hard drive failures, power outages and overheating.

The Anvil! Platform developed by Alteeve's Niche! improves upon traditional approaches to high-availability by making autonomous intelligent decisions and offering complete redundancy with a unique and specific arrangement of hardware devices.

Alteeve’s infrastructure is comprised of two management servers called Striker, two UPSes, two PDU’s, two Switches, and two sets
of Nodes running client's VMs (whatever servers/services you might want to protect). One of the objectives of SimEngine project is to accurately recreate behaviour of core hardware assets and simulate their power connections.

![Alteeve's Hardware Comprised of redundant nodes](./alteeveHardware.png)

To draw a meaningful conclusion from the state of the system, Anvil's agents collect all sorts of data from its devices including:

*  Battery level of the UPSes
*  Load on PDUs & UPSes
*  States of RAID arrays in a server
*  Whether a particular device is up & running
*  ..And all sorts of other things

This information is exposed by hardware itself through either SNMP interface for assets like Switches, PDUs, UPSes, or through IPMI interface for nodes supporting a [BMC chip](https://www.servethehome.com/explaining-the-baseboard-management-controller-or-bmc-in-servers/).

![Communication within Anvil](./alteeveHardwareInterface.png)

Hardware data produced by the simulation engine is exposed through IPMI & SNMP interfaces the same way real physical components present their states. SimEngine is using 3rd party packages for its network simulations including [OpenIPMI's](https://sourceforge.net/projects/openipmi/) lanserv and [snmpsim](http://snmplabs.com/snmpsim/simulating-agents.html) tool for SNMP interface.

Anvil's hardware, for which we use term 'Assets', is stored internally as a graph where each node can be powered by another node (or multiple nodes in some cases). This allows engine to accept complex and diverse arrangements of hardware not limited to Alteeve's system layout. The power connections between nodes are used to infer power & load behaviour within the system.

![SimEngine's representation of Anvil!](./simHardware.png)

In addition to that, SimEngine supports both web-based management dashboard as well as a set of command line tools aimed to automate continuous testing.

