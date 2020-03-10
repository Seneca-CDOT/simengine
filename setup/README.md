# SimEngine setup scripts

## Important notes
* These scripts and instructions are based on Fedora 30.

## SE installation scripts

`./install-simengine/execute` will execute the following scripts in order:
1. `add-neo4j-repo`
2. `install-rpms`

## SE setup anvil scripts

### Prerequisites
* Before the setup, make sure your Fedora machine is using Xorg instead of Wayland for display; see [this link](https://docs.fedoraproject.org/en-US/quick-docs/configuring-xorg-as-default-gnome-session/ "Configuring Xorg as the default GNOME session")

`./setup-anvil/execute` will execute the following scripts in order:
1. `create-striker-iso`
2. `install-virtualization`
3. `create-networks`
4. `create-vms`
5. `config-host-network`
6. `open-ports`
7. `model-anvil`
