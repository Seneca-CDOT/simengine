# Anvil Model

Simengine can support various topology layouts; In this section we will attempt to model [alteeve’s](https://www.alteeve.com/c/) high-availability system called _Anvil_ which consists of 2 striker dashboard machines, 2 target servers with IPMI interface, 2 PDUs, 2 Switches and 2 UPSes. High-level system map can be found on alteeve’s wiki [page](https://www.alteeve.com/w/Build_an_m2_Anvil!#Logical_Map.3B_Hardware_And_Plumbing).

This table summarises the general layout of the `simengine` system model we are going to configure:

| **key** | **Name**     | **Type**   | **Interface**                                        |
| ------- | ------------ | ---------- | ---------------------------------------------------- |
| 1       | outlet-1     | outlet     |                                                      |
| 2       | outlet-2     | outlet     |                                                      |
| 3       | ups01        | ups        | SNMP → reachable at 192.168.124.3 (default port 161) |
| 4       | ups02        | ups        | SNMP → reachable at 192.168.124.4                    |
| 5       | pdu01        | pdu        | SNMP → reachable at 192.168.124.5                    |
| 6       | pdu02        | pdu        | SNMP → reachable at 192.168.124.3                    |
| 7       | an-a01n01    | server-bmc | IPMI → reachable at localhost:9001 (or from the VM)  |
| 8       | an-a01n02    | server-bmc | IPMI → reachable at localhost:9101 (or from the VM)  |
| 9       | an-striker01 | server     |                                                      |
| 10      | an-striker02 | server     |                                                      |

4 VMs will be running so the host machine should preferably have more than 4 cores.

## Network Configuration

We will need to allocate IP addresses for the SNMP simulators on the host machine (machine that will run `simengine`). In this example, we will temporarily add IP addresses to the existing `enp4s0` interface:

    sudo ip addr add dev enp4s0 192.168.124.3/24 # UPS 1
    sudo ip addr add dev enp4s0 192.168.124.4/24 # UPS 2
    sudo ip addr add dev enp4s0 192.168.124.5/24 # PDU 1
    sudo ip addr add dev enp4s0 192.168.124.6/24 # PDU 2

!!! note ""
    You may need to re-configure your firewall and expose port 161 to the striker systems.

## VM

4 VMs will be managed by the simulation engine — `an-a01n01` & `an-a01n02` will be running Fedora 28 and striker dashboards (`an-striker01` & `an-striker02`) will be hosted on CentOS-based system.

    [root@narnia enginecore]# virsh list --all
    Id    Name                           State
    ----------------------------------------------------
    -     an-a01n01                      shut off
    -     an-a01n02                      shut off
    -     an-striker01                   shut off
    -     an-striker02                   shut off

The installation of the VMs plus minor setup need to be performed prior to the system modelling stage.

### BMC and storcli64

Since 2 VMs ( `an-a01n01` & `an-a01n02` ) will support BMC/IPMI interface and storcli64, we will need to have lanplus interface and qemu options configured;

Once you install the target operating systems, shut down the VMs and configure `.xml` args as following:

**an-a01n01**

Update `.xml` configurations:

`sudo virsh edit an-a01n01`

You will need to change the top-level tag to `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>` and also add `qemu` command line arguments (after `</devices>`):

    <qemu:commandline>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=ipmi0,host=localhost,port=9002,reconnect=10'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='ipmi-bmc-extern,id=bmc0,chardev=ipmi0'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='isa-ipmi-bt,bmc=bmc0'/>
        <qemu:arg value='-serial'/>
        <qemu:arg value='mon:tcp::9012,server,telnet,nowait'/>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=simengine-storage-tcp,host=localhost,port=50000,reconnect=2'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtio-serial'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtserialport,chardev=simengine-storage-tcp,name=systems.cdot.simengine.storage.net'/>
    </qemu:commandline>

**an-a01n02**

Almost identical steps need to be performed for the second VM (note that ipmi socket is assigned a different port this time (`port=9102`) which we will later pass as one of the command line arguments to `simengine-cli`).

`sudo virsh edit an-a01n02`

Change the top-level tag to `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>` , add `qemu` command line arguments (after `</devices>`) as following:

    <qemu:commandline>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=ipmi0,host=localhost,port=9102,reconnect=10'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='ipmi-bmc-extern,id=bmc0,chardev=ipmi0'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='isa-ipmi-bt,bmc=bmc0'/>
        <qemu:arg value='-serial'/>
        <qemu:arg value='mon:tcp::9012,server,telnet,nowait'/>
        <qemu:arg value='-chardev'/>
        <qemu:arg value='socket,id=simengine-storage-tcp,host=localhost,port=50001,reconnect=2'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtio-serial'/>
        <qemu:arg value='-device'/>
        <qemu:arg value='virtserialport,chardev=simengine-storage-tcp,name=systems.cdot.simengine.storage.net'/>
    </qemu:commandline>

**storcli64**

You will need to upload `storcli64` binary to the target vms (`an-a01n01` and `an-a01n02`) bin folder `/usr/bin` and make them executable by running `chmod +x /usr/bin/storcli64`.

The binary can be found in simengine repo: [link](https://github.com/Seneca-CDOT/simengine/blob/master/storage-emulation-tests/guest/storcli64)

## System Model

At this stage, we should be ready to model our HA topology. You will need to drop the existing model in case the data store is not empty:

`simengine-cli model drop`

And pause the engine daemon:

`sudo systemctl stop simengine-core`

Running the source code below should re-create the Anvil topology; `model create` will add new assets to the data store & `model power-link` will link assets together:

    # Create 2 outlets, one powers 'an-ups01' another one powers 'an-ups02'
    simengine-cli model create outlet --asset-key=1 -x=-861 -y=-171
    simengine-cli model create outlet -k2 -x=-861 -y=351

    # Add 2 UPSs
    simengine-cli model create ups -k=3 --name=an-ups01 --host=192.168.124.3 --port=161 -x=-895 -y=-182
    simengine-cli model create ups -k=4 --name=an-ups02 --host=192.168.124.4 --port=161 -x=-895 -y=347

    # Create 2 PDUs
    simengine-cli model create pdu -k=5 -n=an-pdu01 --host=192.168.124.5 --port=161 -x=-36 -y=-161
    simengine-cli model create pdu -k=6 -n=an-pdu02 --host=192.168.124.6 --port=161 -x=-36 -y=567

    # Add 2 Servers
    simengine-cli model create server-bmc -k=7 --domain-name=an-a01n01 --power-consumption=360 -x=-162 -y=320
    simengine-cli model create server-bmc -k=8 --domain-name=an-a01n02 --power-consumption=360 --port=9101 --vmport=9102 --storcli-port=50001 -x=-171 -y=86

    # Add 2 Striker Servers
    simengine-cli model create server -k=9 --domain-name=an-striker01 --power-consumption=240 --psu-num=1 -x=738 -y=101
    simengine-cli model create server -k=10 --domain-name=an-striker02 --power-consumption=240 --psu-num=1 -x=734 -y=326

    ### Power Components
    # connect outlets & UPSs
    simengine-cli model power-link -s1 -d3   # {_Mains_}==>[an-ups01]
    simengine-cli model power-link -s2 -d4   # {_Mains_}==>[an-ups02]

    # connect ups & pdus
    simengine-cli model power-link -s31 -d5  # [an-ups01]==>[an-pdu01]
    simengine-cli model power-link -s41 -d6  # [an-ups02]==>[an-pdu02]

    # Power up servers
    simengine-cli model power-link -s51 -d72 # [an-pdu01]={port-1}=>{psu-2}=>[an-a01n01]
    simengine-cli model power-link -s52 -d82 # [an-pdu01]={port-2}=>{psu-2}=>[an-a01n02]

    simengine-cli model power-link -s61 -d71 # [an-pdu02]={port-1}=>{psu-1}=>[an-a01n01]
    simengine-cli model power-link -s62 -d81 # [an-pdu02]={port-2}=>{psu-1}=>[an-a01n02]

    # Power Up Striker Servers
    simengine-cli model power-link -s58 -d91 # [an-pdu01]={port-1}=>{psu-2}=>[an-a01n01]
    simengine-cli model power-link -s68 -d101 # [an-pdu02]={port-1}=>{psu-1}=>[an-a01n01]

Re-start the daemon:
`sudo systemctl start simengine-core`

You can verify that the simulators are running by issuing:

`ps aux | grep snmpsimd # should show 4 instances`

`ps aux | grep ipmi_sim # should show 2 instances`

## First Run

The front-end web-page will display assets in the following arrangement:

![](./anvil.png)

You can customize the layout by positioning the assets in the preferred way. Click on gear ⚙️ icon & choose ‘Save Layout’ to save new asset coordinates;

![](https://d2mxuefqeaa7sj.cloudfront.net/s_C5C75BF29B870479D1EC95201C69BB583A74A130BB1FC9890A125939ED904715_1534526478583_s.png)

## Management

**UPS**

UPSes’ SNMP interface can be reached at `192.168.124.3` & `192.168.124.4`

For example:

`snmpwalk -Cc -c public -v 1 192.168.124.3 .1.3.6.1.4.1.318.1.1.1.2.2`

`snmpwalk -Cc -c public -v 1 192.168.124.4 .1.3.6.1.4.1.318.1.1.1.2.2`

More documentation on UPS management can be found here: [link](https://simengine.readthedocs.io/en/latest/AssetsConfigurations/#ups);

**PDU**

PDUs SNMP interface is accessible at `192.168.124.5` & `192.168.124.6`

For example:

`snmpwalk -Cc -c public -v 1 192.168.124.5`

`snmpwalk -Cc -c public -v 1 192.168.124.6`

**Server-BMC**

Servers that support BMC interface can be accessed from both host machine & the VMs:

Running from host example:

`ipmitool -H localhost -p 9001 -U ipmiusr -P test sdr list # server 7 (an-a01n01)`

`ipmitool -H localhost -p 9101 -U ipmiusr -P test sdr list # server 8 (an-a01n02)`

VM:

`sudo ipmitool sdr list`

**storcli64**

You can test `storcli64` from one of the vms (`an-a01n01` or `an-a01n02`) by running:

`storcli64 /c0 show all`

**Power Management**

You can retrieve status of individual assets by issuing:

`simengine-cli status -k1 # is out-1 up?`

And power them up/down:

`simengine-cli power down -k1 # out-1 is down`

More information on asset management including storage and thermal relationships can be found here: [link](./Asset%20Management);

**Model Updates**

You can update the existing model (for example, update UPS snmp ip address or server’s power consumption);

!!! note ""
    Any model changes require `simengine-core` service restart;

see `simengine-cli model update` for more information;
