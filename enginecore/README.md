## Setting Up

### Install and configure

Run the installation script:
'script/simengine-setup'

This will run the series of scripts in script/setup/

Note that some components are not yet packaged as RPMs,
and these components are installed from other sources
(e.g., pip). Note also that additional repositories may
be added to the system's yum/dnf configuration by this
script.

## Run

Run the script:
'script/simengine-run'

## VM with BMC

Server with IPMI_SIM support (`serverbmc`) requires specific `.xml` configurations for qemu VM. You can edit `libvirt` config file 
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

## System Modelling

### Creation

`simengine-cli` provides interface for making your own model (run `simengine-cli model --help` for more information). You can also define the system topology directly through `cypher`  & `neo4j` interface (see examples in `topologies` folder).

The simplest example would be a model that is composed of a single pdu powered by an outlet:

    simengine-cli model create --asset-key=1111 --asset-type=outlet
    simengine-cli model create --asset-key=1112 --asset-type=pdu
    simengine-cli model power-link --source-key=1111 --dest-key=1112

The code snippet below will create more complicated system that includes 3 PDUs and some static assets drawing power from the power distribution devices. Note that the main engine daemon will need to be reloaded before schema changes can take place.

![](https://d2mxuefqeaa7sj.cloudfront.net/s_CC16473B6C5F58570EB58EA5E80058A0D480F8E0A83C2F210CA8B571B2BEB5FA_1530046389520_sample.png)


Source Code:


    # Create an Outlet
    simengine-cli model create --asset-key=1111 --asset-type=outlet
    
    # Create 3 PDUs
    simengine-cli model create --asset-key=1112 --asset-type=pdu
    simengine-cli model create --asset-key=1113 --asset-type=pdu
    simengine-cli model create --asset-key=1114 --asset-type=pdu
    
    # Add bunch of microwaves (4 items)
    simengine-cli model create --asset-key=2011 --asset-type=static --name='Panasonic' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create --asset-key=2012 --asset-type=static --name='EvilCorp' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create --asset-key=2013 --asset-type=static --name='EvilCorp 10' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    simengine-cli model create --asset-key=2014 --asset-type=static --name='EvilCorp 10' --img-url=http://z3central.cdot.systems/docs/microwave-159076_640.png --power-source=120 --power-consumption=600
    
    # Linking Assets Together
    simengine-cli model power-link --source-key=1111 --dest-key=1112
    simengine-cli model power-link --source-key=11124 --dest-key=1113
    simengine-cli model power-link --source-key=11138 --dest-key=1114
    simengine-cli model power-link --source-key=11141 --dest-key=2011
    simengine-cli model power-link --source-key=11143 --dest-key=2012
    simengine-cli model power-link --source-key=11133 --dest-key=2013
    simengine-cli model power-link --source-key=11127 --dest-key=2014
    


### Updating the Model

Some properties can be configured later as in this example:

`simengine-cli model configure --asset-key=1113 --off-delay=3000 #set power-off delay as 3000 ms`

The entire system topology can be deleted with `simengine-cli model drop` command

You can also remove & detach specific assets by key (note that you may need to re-connect some assets afterwards):

`simengine-cli model delete --asset-key=1113`

## Linting

`sudo python3 -m pip install pylint`

This lintrc file is based on Google Style Guide. See this docstring [example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for documentation format reference.


## Sample Unit test invocation

`python3 -m unittest tests.server_load_m1`