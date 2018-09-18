# Release - RPM

Simengine project is packaged as RPM. You can retrieve the project specs by downloading the repo details from the project repository:

`wget https://raw.githubusercontent.com/Seneca-CDOT/simengine/master/rpm/simengine.repo`

`cp simengine.repo /etc/yum.repos.d/`

Install app's core components:

`dnf install simengine-database simengine-core simengine-dashboard`


# Development Version

## DNF Dependencies 

Simengine uses OpenIPMI lanserv simulator for its BMC emulations and libvirt for virtualization.

```
dnf install libvirt OpenIPMI OpenIPMI-lanserv OpenIPMI-libs OpenIPMI-devel python3-libvirt -y
dnf install gcc redis -y
```

## Neo4J

For Neo4J installation, see this official [page](https://neo4j.com/docs/operations-manual/current/installation/linux/rpm/)

You will need to create a `simengine` user (see [link](https://neo4j.com/docs/operations-manual/current/reference/user-management-community-edition/)).

## ipmi_sim

`hoas_extend` is a plugin built for `ipmi_sim`.

Change location to `enginecore/ipmi_sim`

Build the extension:

`gcc -shared -o ./haos_extend.so -fPIC ./haos_extend.c`

Move to lib folder (may be arch-dependent):

`sudo mkdir /usr/lib64/simengine`

`sudo cp ./haos_extend.so  /usr/lib64/simengine`

## enginecore

Change location to `enginecore`

Install pip packages: 

`python3 -m pip install -r requirements.txt`

Install `snmpsimd` (python2 version):

`pip install snmpsim`

## Frontend

Change location to `dashboard/fronend`

Run `npm install` and then `npm start`

## Running

`simengine-cli` will need to be put into `$PATH` as `export PATH="$PATH:/path/to/simengine/enginecore"`

You can start the main daemon (as root) by issuing:

`./app.py -d -r -v`

