# Simengine Demo

Resources for demoing the simengine / anvil dashboards

## Aquiring and running simengine-demo script

### Installing simengine repo file:
```bash
sudo dnf install http://england.cdot.systems/simengine/simengine-repo-3.42-1.fc35.noarch.rpm
```

### Installing simengine-demo script and desktop file:
```bash
sudo dnf install simengine-demo
```

### Downloading and unpacking simengine vm:

Command line:
```bash
simengine-demo --download
```

Desktop file:
```
right click, select "Download"
```

Note: Through the command line you will be able to monitor progress of the download, through the desktop file this feature is absent at the momment.


## Setting up simengine

command line: 
```bash
simengine-demo --setup
```

desktop file: 
```
right click, select "Setup"
```

## Accessing the simengine and anvil dashboards

Assuming all has went well, all that's left any time you would like to access the dashboard is:
    
command line:
```bash
simengine-demo
```

desktop file:
```
open the desktop file normally
```

Upon success you should have two browser tabs opened to the simengine and anvil dashboards, all done!


## Additional notes

The startup process can take anywhere between 4-10 minutes, it takes time for each system and necessary service to get started.

If the startup fails and ends with the error message "Inner vms unreachable" it's best to shut down the simengine vm and try again.

You can shut it down with ``` simengine-demo --shutdown ```, right clicking the desktop file and selecting "Shutdown", or through virsh yourself targeting "simengine"

Once that's done, simply try again


Details for additional options available through "simengine-demo -h'

