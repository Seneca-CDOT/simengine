# simengine-rpm
RPM packaging for the SimEngine project.

To build all of the RPMs, set the Version: in the spec files to a version
that is tagged in the GitHub repo, then run:

	 ${GitRepoBase}/rpm/specfiles/buildall

To install from RPMs:

Installation from RPM:
(1) Add the neo4j repository as documented at http://yum.neo4j.org/stable/

(2) Install the local simengine RPMs from the local repository: 
	
	sudo dnf install *.rpm

