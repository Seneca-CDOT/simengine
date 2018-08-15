
# Asset Configurations

## UPS
 
You can update UPS runtime chart http://www.apcguard.com/Smart-UPS-Runtime-Chart.asp

`simengine-cli model update ups -k2 --runtime-graph "$(cat /tmp/runtime.json)`
    
## Server Type

Server asset can manage VMs state and control its power. It supports up to 2 PSUs at the moment and requires power consumption and valid VM domain name specified (`--domain-name={my_vm}` argument).

Server with IPMI_SIM interface (`server-bmc`) requires specific `.xml` configurations for qemu VM. You can edit `libvirt` config file 
by issuing this command:

`virsh edit {domain name}`

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

