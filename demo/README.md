# Simengine Demo


For anyone looking to demo or test an example of [Simengine](https://github.com/Seneca-CDOT/simengine) running with the [Alteeve Anvil model](https://simengine.readthedocs.io/en/latest/Anvil%20Model/).

A bash script and desktop file providing CLI and GUI options for downloading and setting up a virtual environment that is pre-configured for simengine, running an example of the Anvil model. The script also provides access to the simengine dashboard for managing the model through GUI, as well as the Anvil! dashboard.

### System Requirements

Fedora Linux 35+

32GB RAM

150GB+ available storage space

[libvirt](https://libvirt.org/) installed

## Acquiring and running simengine-demo script

For users that prefer working through the linux command line [follow these instructions](#CLI-based-Installation).

For users that prefer working through GUI [follow these instructions](#GUI-based-Installation).


### CLI-based Installation


#### 1. Installing simengine repo file

Executing this command in your terminal will install a repo file for simengine, providing [DNF](https://docs.fedoraproject.org/en-US/quick-docs/dnf/) access to the rpm package for simengine-demo and additional simengine packages, should you wish to install them.

```bash
sudo dnf install http://england.cdot.systems/simengine/simengine-repo-3.42-1.fc35.noarch.rpm
```

#### 2. Installing simengine-demo

With the repo file installed, execute this command to install the rpm package for simengine-demo:

```bash
sudo dnf install simengine-demo
```

#### 3. Downloading simengine vm image

With the previous package installed, you now have access to the simengine-demo script.

Execute the following command to begin downloading the simengine virtual machine image, you can monitor the progress in the terminal.

```bash
simengine-demo --download
```

#### 4. Setting up simengine

Next execute this command to install the simengine VM with the image downloaded:

```bash
simengine-demo --setup
```

#### 5. Accessing the simengine and anvil dashboards

Executing the simengine-demo script with no additional options will start the simengine VM, and begin the process of verifying the status of the Anvil model simulation, completing by opening the Simengine and Anvil! dashboards.

Execute this command to get started:

```bash
simengine-demo
```

NOTE: The startup process can take anywhere between 4-10 minutes, it takes a significant amount of time for each system and necessary service to get started.

Upon success you should have two browser tabs opened to the simengine and anvil dashboards, all done!

#### 6. Shutting down the simengine VM

If the startup fails and ends with the error message "Inner vms unreachable" it's best to shut down the simengine vm and try again.

You can shut it down by executing the command:

```bash
simengine-demo --shutdown
```

**IMPORTANT**: Remember to also shut down any time you are done working with the VM and the dashboards.

### GUI-based Installation

#### 1. Installing simengine-demo

[Click here](http://england.cdot.systems/simengine/simengine-demo-3.42-1.fc36.noarch.rpm) to download an rpm package containing the simengine-demo script, open the rpm package, and install via "Software Install"

This rpm package will install a desktop file named "simengine-demo", this can be found in the applications menu for your machine. This file will be used to download, install, and manage the simengine virtual machine.

#### 2. Downloading simengine VM image

Using the simengine-demo desktop file installed in the last step:

```
right click, select "Download"
```

Note: Through the command line you will be able to monitor progress of the download, through the desktop file this feature is absent at the momment.

#### 3. Setting up simengine

Using the simengine-demo desktop file to install the VM with the image downloaded:

```
right click, select "Setup"
```

#### 4. Accessing the simengine and anvil dashboards

Opening simengine-demo normally will start the simengine VM, and begin the process of verifying the status of the Anvil model simulation, completing by opening the Simengine and Anvil! dashboards.

```
simply left click the desktop file
```
NOTE: The startup process can take anywhere between 4-10 minutes, it takes a significant amount of time for each system and necessary service to get started.

Upon success you should have two browser tabs opened to the simengine and anvil dashboards, all done!

#### 5. Shutting down the simengine VM

If the startup fails and ends with the error message "Inner vms unreachable" it's best to shut down the simengine VM and try again. You can shut it down through the the desktop file: 
```
right click, select "Shutdown"
```
**IMPORTANT**: Remember to also shut down any time you are done working with the VM and the dashboards.