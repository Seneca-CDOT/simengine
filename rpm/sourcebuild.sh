#!/bin/bash

# Archives SimEngine source files from local Git to tarball in ~/rpmbuilds/SOURCES/

core () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-core-1.tar.gz ~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ ~/Documents/Alteeve/SimEngine/Git\ Code/services/simengine-core.service
}

frontend () {
	
}