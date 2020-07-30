# simengine-rpm
RPM packaging for the SimEngine project.


Fedora 31+
----------

This software has a temporary build dependency on python2. While Fedora 31/32
includes the python27 package, the corresponding -devel package is not included.
To build the required packages, build the SRPMs in the srpm/ subdirectory and
install the resulting packages. It is recommended that you do this using 'mock'.



All Versions
------------

To the RPMs, first set the Version: in the spec files to a version that is 
tagged in the GitHub repo (i.e., create a tag for version 20.6, and set
Version: in the simengine\* spec files to 20.6). This can be done using the
'newtag' script:

	${GitRepoBase}/rpm/specfiles/newtag


Then run:

	 ${GitRepoBase}/rpm/specfiles/buildall

To install from RPMs:

(1) Add the neo4j repository as documented at http://yum.neo4j.org/stable/

(2) Install the local simengine RPMs from the local repository: 
	
	sudo dnf install *.rpm

