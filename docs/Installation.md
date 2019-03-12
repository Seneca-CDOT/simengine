## Release - RPM


To install from RPMs:

1) Add the neo4j repository as documented at [http://yum.neo4j.org/stable/](http://yum.neo4j.org/stable/)

2) Build local RPMs from specs by running [buildall script](https://github.com/Seneca-CDOT/simengine/tree/master/rpm/specfiles) 

3) Install the local simengine RPMs from the local repository: 
	
	sudo dnf install *.rpm

### Packaging

RPM packaging for the SimEngine project.

To build all of the RPMs, first set the Version: in the spec files to a version
that is tagged in the GitHub repoi (i.e., create a tag for version 20.6, and set
Version: in the simengine\* spec files to 20.6), then run:

	 ${GitRepoBase}/rpm/specfiles/buildall


## Python API

Some SimEngine functionalities, including power management, storage and thermal settings, can be utilized through python api:

```
from enginecore.state.api import IStateManager as State
from enginecore.state.assets import SUPPORTED_ASSETS

# get pdu 4 and power it down
pdu_4_sm = State.get_state_manager_by_key(4, SUPPORTED_ASSETS)
pdu_4_sm.shut_down()
```

### Installation

The easiest way to install package is to download it from PyPI:

`python3 -m pip install simengine`


## Development Version

### DNF Dependencies 

Simengine uses OpenIPMI lanserv simulator for its BMC emulations and libvirt for virtualization.

```
dnf install libvirt OpenIPMI OpenIPMI-lanserv OpenIPMI-libs OpenIPMI-devel python3-libvirt -y
dnf install gcc redis -y
dnf install ipmitool -y #for testing
```

### Neo4J

For Neo4J installation, see this official [page](https://neo4j.com/docs/operations-manual/current/installation/linux/rpm/)

You will need to create a `simengine` user (see [link](https://neo4j.com/docs/operations-manual/current/reference/user-management-community-edition/)).

### ipmi_sim

`hoas_extend` is a plugin built for `ipmi_sim`.

Change location to `enginecore/ipmi_sim`

Build the extension:

`gcc -shared -o ./haos_extend.so -fPIC ./haos_extend.c`

Move to lib folder (may be arch-dependent):

`sudo mkdir /usr/lib64/simengine`

`sudo cp ./haos_extend.so  /usr/lib64/simengine`

### enginecore

Change location to `enginecore`

Install pip packages: 

`python3 -m pip install -r requirements.txt`

Install `snmpsimd` (python2 version):

`pip install snmpsim`

### Frontend

Change location to `dashboard/fronend`

Run `npm install` and then `npm start`

### MIBs

Vendor-specific mibs may need to be installed for the testing purposes.

`dnf install net-snmp net-snmp-utils`

Add mib definitions:

`mkdir /usr/share/snmp/mibs/apc`

`cp data/ups/powernet426.mib /usr/share/snmp/mibs/apc/ # copy from simengine project`

Create configuration file:

`vi /etc/snmp/snmp.conf`

Paste `mibdirs` reference:

```
mibdirs /usr/share/snmp/mibs:/usr/share/snmp/mibs/apc
mibs ALL
```

### Running

`simengine-cli` will need to be put into `$PATH` as `export PATH="$PATH:/path/to/simengine/enginecore"`

You can start the main daemon (as root) by issuing:

`./app.py -d -r -v`

