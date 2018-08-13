# System Modelling

`simengine-cli` provides interface for making your own system model (run `simengine-cli model --help` for more information). You can also define the system topology directly through `cypher`  & `neo4j` interface (see examples in `topologies` folder).
There're 6 supported asset types at the moment: Outlet, PDU, UPS, Server, Server with BMC (IPMI interface) and Static Device (dummy asset). The CLI type options can be found under `simengine-cli model create -h`.

*Note* that the main engine daemon will need to be reloaded before schema changes can take place.

The first time you load the model in a web interface, the assets are going to be overlayed on top of each other. You will need to create your own layout by dragging the components around, clicking `Gear` icon located in the top bar and saving it by choosing `Save Layout` option.

Note that the UI does not support system modelling tools at the moment.

## Creation

You can create a new asset with `model create` and power it by another asset with `model power-link`, The simplest example would be a model that is composed of a single pdu powered by an outlet:

    simengine-cli model create outlet --asset-key=1111
    simengine-cli model create pdu --asset-key=1112
    simengine-cli model power-link --source-key=1111 --dest-key=1112

The code snippet below will create more complicated system that includes 3 PDUs and some static assets drawing power from the power distribution devices.

![](./pdu_rack.png)


Source Code:


    # Create an Outlet
    simengine-cli model create outlet --asset-key=1111
    
    # Create 3 PDUs
    simengine-cli model create pdu --asset-key=1112 
    simengine-cli model create pdu --asset-key=1113 
    simengine-cli model create pdu --asset-key=1114 
    
    # Add bunch of microwaves (4 items)
    simengine-cli model create static --asset-key=2011 --name='Panasonic' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create static --asset-key=2012 --name='EvilCorp' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create static --asset-key=2013 --name='EvilCorp 10' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create static --asset-key=2014 --name='EvilCorp 10' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    
    # Linking Assets Together
    simengine-cli model power-link --source-key=1111 --dest-key=1112
    simengine-cli model power-link --source-key=11124 --dest-key=1113
    simengine-cli model power-link --source-key=11138 --dest-key=1114
    simengine-cli model power-link --source-key=11141 --dest-key=2011
    simengine-cli model power-link --source-key=11143 --dest-key=2012
    simengine-cli model power-link --source-key=11133 --dest-key=2013
    simengine-cli model power-link --source-key=11127 --dest-key=2014
    
    
### Server Type

Server asset can manage VMs state and control its power. It supports up to 2 PSUs at the moment and requires power consumption and valid VM domain name specified (`--domain-name={my_vm}` argument).

Server with IPMI_SIM interface (`server-bmc`) requires specific `.xml` configurations for qemu VM. You can edit `libvirt` config file 
by issuing this command:

`virsh edit {{domain name}}`

You will need to change the top-level tag to `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>` and also add `qemu` command line arguments (after `</devices>`) as following:


    <qemu:commandline>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=ipmi0,host=localhost,port=9002,reconnect=10'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='ipmi-bmc-extern,id=bmc0,chardev=ipmi0'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='isa-ipmi-bt,bmc=bmc0'/>
        <qemu:arg value='-serial'/>
        <qemu:arg value='mon:tcp::9012,server,telnet,nowait'/>
    </qemu:commandline>



Here's a sample model consisting of 2 outlets, 1 PDU, microwave and a server (controlling a VM named `fedora27`):

    # Create 2 outlets, one powers PDU another one powers PSU2
    simengine-cli model create outlet --asset-key=1
    simengine-cli model create outlet --asset-key=2

    # Add a PDU 
    simengine-cli model create pdu --asset-key=3 
   
    # Add one useless microwave
    simengine-cli model create static --asset-key=4 --name='Panasonic' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=120

    # Add server that supports BMC & IPMI
    simengine-cli model create server-bmc -k=5 --domain-name=fedora27 --power-consumption=480 --psu-num=2 --psu-load 0.5 0.5

    # Power up the components
    simengine-cli model power-link --source-key=1 --dest-key=3
    simengine-cli model power-link --source-key=31 --dest-key=4
    simengine-cli model power-link --source-key=35 --dest-key=51
    simengine-cli model power-link --source-key=2 --dest-key=52


The IPMI interface can be queried as:

`ipmitool -H localhost -p 9001 -U ipmiusr -P test sdr list`

`ipmitool -H localhost -p 9001 -U ipmiusr -P test power status`

SNMP interface can be queried as:

`snmpget -c public -v 1 127.0.0.1:1024  1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.3`

`snmpwalk -c public -v 1 127.0.0.1:1024`

## Updating the Model

Some properties can be configured later as in this example:

`simengine-cli model configure --asset-key=1113 --off-delay=3000 # set power-off delay as 3000 ms`

The entire system topology can be deleted with `simengine-cli model drop` command

You can also remove & detach specific assets by key (note that you may need to re-connect some assets afterwards):

`simengine-cli model delete --asset-key=1113`