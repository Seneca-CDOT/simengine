# SimEngine RPM

RPM packaging for the SimEngine project.

To build all of the RPMs, first set the Version: in the spec files to a version
that is tagged in the GitHub repo (i.e., create a tag for version 20.6, and set
Version: in the simengine\* spec files to 20.6), then run:

     ${GitRepoBase}/rpm/specfiles/buildall

To install from RPMs:

1. Add the neo4j repository as documented at http://yum.neo4j.org/stable/. Neo4j 4.x.x is not compatible with SimEngine; Neo4j 3.x.x (likely 3.5.14) should be used. Refer to [add-neo4j-repo](../setup/install-simengine/add-neo4j-repo) for adding the corresponding repository.

2. Install the local simengine RPMs from the local repository:
sudo dnf install \*.rpm

Note: when installing SimEngine for CI purpose, i.e., interaction with SimEngine is only done through command line, the dashboard package is probably unnecessary.

## For CentOS 8 Stream

### Build Prerequisites

1. Enable EPEL

```
sudo dnf install epel-release
```

2. Enable PowerTools

```
sudo dnf config-manager --set-enabled powertools
```

3. When starting with a fresh CentOS installation, Set nodejs module to the nodejs:12 stream using:

```
# Remove all packages provided by the nodejs:10 stream (major version 10).
sudo dnf module remove --all nodejs:10

# Sets all nodejs streams to neither enabled or disabled state to avoid conflicts.
sudo dnf module reset nodejs

# Switch to the nodejs:12 stream (major version 12) to meet the minimum requirement for building simengine-dashboard.
sudo dnf module switch-to nodejs:12
```
