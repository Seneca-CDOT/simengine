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



## Linting

`sudo python3 -m pip install pylint`

This lintrc file is based on Google Style Guide. See this docstring [example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for documentation format reference.


## Sample Unit test invocation

`python3 -m unittest tests.server_load_m1`