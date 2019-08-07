## Release - RPM

To install from RPMs:

1. Add the neo4j repository as documented at [http://yum.neo4j.org/stable/](http://yum.neo4j.org/stable/)

2. Build local RPMs from specs by running [buildall script](https://github.com/Seneca-CDOT/simengine/tree/master/rpm/specfiles)

3. Install the local simengine RPMs from the local repository:
   sudo dnf install \*.rpm

### Packaging

RPM packaging for the SimEngine project.

To build all of the RPMs, first set the Version: in the spec files to a version
that is tagged in the GitHub repoi (i.e., create a tag for version 20.6, and set
Version: in the simengine\* spec files to 20.6), then run:

     cd ${GitRepoBase)/rpm/specfiles
     ./buildall

### Building New RPMs

To build a new set of RPMs, run the newtag script:

     cd ${GitRepoBase}/rpm/specfiles
     ./newtag

This will bump the product tag and adjust the Version: tags in the spec files, committing all of the changes to origin. Next, push both the code changes and the tag:

     git push
     git push --tag

## Licenses

SimEngine is licensed under [GPL V3](https://github.com/Seneca-CDOT/simengine/blob/master/LICENSE.txt);

**Dependencies**

Here’s a list of RPM packages used by the project and their licenses:

```
python2-snmpsim: BSD
python3-circuits: MIT
python-snmpsim-doc: BSD
python3-neo4j-driver: Apache License, Version 2.0
OpenIPMI-libs: LGPLv2+ and GPLv2+ or BSD
OpenIPMI-lanserv: LGPLv2+ and GPLv2+ or BSD
OpenIPMI: LGPLv2+ and GPLv2+ or BSD
OpenIPMI-devel: LGPLv2+ and GPLv2+ or BSD
redis: BSD and MIT
```

SimEngine is using Neo4j Community Edition ([GPL v3 license](http://www.gnu.org/licenses/quick-guide-gplv3.html)), licensing details can found on this official neo4j support [page](https://neo4j.com/licensing/).

Python PIP Dependencies:

-   [[repo](https://github.com/andymccurdy/redis-py)/[pip](https://pypi.org/project/redis/)] **redis-py** (redis python client, licensed under [MIT](https://github.com/andymccurdy/redis-py/blob/master/LICENSE))
-   [[repo](https://github.com/circuits/circuits)/[pip](https://pypi.org/project/circuits/)] **circuits** (event-driven framework, licensed under [MIT](https://github.com/circuits/circuits/blob/master/LICENSE))
-   [[repo](https://github.com/neo4j/neo4j-python-driver)/[pip](https://pypi.org/project/neo4j-driver/)] **neo4j-driver** - (neo4j database client, licensed under [Apache 2.0](https://github.com/neo4j/neo4j-python-driver/blob/2.0/LICENSE.txt))
-   [[repo](https://github.com/etingof/pysnmp)/[pip](https://pypi.org/project/pysnmp/)] **pysnmp** - (SNMP engine implementation, [BSD 2-Clause "Simplified" License](https://github.com/etingof/pysnmp/blob/master/LICENSE.rst))
-   [[repo](https://libvirt.org/git/?p=libvirt-python.git;a=summary)/[pip](https://pypi.org/project/libvirt-python/)] **libvirt-python** - (libvirt API, GNU LGPL v2 or later (LGPLv2+) (LGPLv2+))
-   [[repo](https://github.com/websocket-client/websocket-client)/[pip](https://pypi.org/project/websocket_client/)] **websocket-client** - (client socket implementation, licensed under [BSD 3-Clause](https://github.com/websocket-client/websocket-client/blob/master/LICENSE))

Dashboard:

A list of frontend npm packages and their corresponding licenses can be found [here](https://github.com/Seneca-CDOT/simengine/blob/master/docs/.misc/frontend-licenses.csv).

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

`sudo cp ./haos_extend.so /usr/lib64/simengine`

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
