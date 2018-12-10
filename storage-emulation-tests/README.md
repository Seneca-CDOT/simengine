storage-emulation-tests
=======================

## Purpose

To provide emulation of a storage controller utility binary within a virtual machine managed by simengine, it is necessary to provide a way for that binary to talk to the simengine. This is a very basic proof-of-concept communication test; it uses a thin wrapper 'binary' within the VM which sends its arguments to simengine via a QEMU virtio-serial port using either a socket or a pipe interface on the host. All processing is done in simengine, which returns the stdout/stderr/status code data for output to the invoking process.

## Sockets vs. Pipes

The software may use sockets or pipes for communication. The socket implementation has some rough edges.

To switch between the two communications techniques, adjust the source code in the host and guest scripts.

## Virsh XML setup (using QEMU-KVM)

* Ensure that the libvirt QEMU schema is included in the XML namespace:
  `<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>`

* For communication via a socket:
  ```
  <qemu:commandline>
    <qemu:arg value='-chardev'/>
    <qemu:arg value='socket,id=simengine-storage-tcp,host=localhost,port=50000,reconnect=10'/>
    <qemu:arg value='-device'/>
    <qemu:arg value='virtio-serial'/>
    <qemu:arg value='-device'/>
    <qemu:arg value='virtserialport,chardev=simengine-storage-tcp,name=systems.cdot.simengine.storage.net'/>
  </qemu:commandline>
  ```

* For communication via a pipe:
  ```
  <qemu:commandline>
    <qemu:arg value='-chardev'/>
    <qemu:arg value='pipe,id=simengine-storage-pipe,path=/tmp/simengine-storage-pipe'/>
    <qemu:arg value='-device'/>
    <qemu:arg value='virtio-serial'/>
    <qemu:arg value='-device'/>
    <qemu:arg value='virtserialport,chardev=simengine-storage-pipe,name=systems.cdot.simengine.storage.pipe'/>
  </qemu:commandline>
  ```
Note that it is OK to enable both configurations in the VM at the same time.

## Communication via pipes

Run simengine-storage-pipe-create as root on the host to create the pipes (required after each reboot since the pipes are in /tmp; they could be moved to another location). This is only required if the pipe communication option is used.

The default pipe name is /tmp/simengine-storage-pipe{"",.in,.out} on the host and the default device name is /dev/virtio-ports/systems.cdot.simengine.storage.pipe in the guest.

Note that the /tmp/simengine-storage-pipe FIFO is required even though the .in and .out files are used for actual communication - virsh/qemu complains if the extensionless file is not present.

## Communication via sockets

The default port is 50000/tcp on the host (via IPv4 localhost), and the default device name is /dev/virtio-ports/systems.cdot.simengine.storage.net in the guest.

## Communicating with Multiple VMs

Since simengine will typically be communicating with multiple VMs, a mechanism is required to keep them separated. Options include:
* using socket communication on different sockets
* using pipe communication with different pipe sets
* sending an identifier with the communication

## SELinux

simengine-storage-pipe-create sets the communications pipes to have type "svirt_image_t", and this solution should be able to run with SELinux fully enabled.

## Permissions

The guest script will need to be run as root. The host portion may be run as any user, providing that if pipes are used the permissions on the pipes in /tmp permit them to be read by the host script.

