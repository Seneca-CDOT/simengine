# simengine-rpm
RPM packaging for the SimEngine project.

To build all of the RPMs, first set the Version: in the spec files to a version
that is tagged in the GitHub repoi (i.e., create a tag for version 20.6, and set
Version: in the simengine\* spec files to 20.6), then run:

	 ${GitRepoBase}/rpm/specfiles/buildall

To install from RPMs:

(1) Add the neo4j repository as documented at http://yum.neo4j.org/stable/

(2) Install the local simengine RPMs from the local repository: 
	
	sudo dnf install *.rpm

