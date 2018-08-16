#!/bin/bash

# Archives SimEngine source files from local Git to tarball in ~/rpmbuilds/SOURCES/

ipmi () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-ipmi-1.tar.gz ~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ipmi_sim ~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ipmi_template
}

cli () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-cli-1.tar.gz ~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/simengine-cli
}

core () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-core-1.tar.gz ~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ --exclude=~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ipmi_sim --exclude=~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/ipmi_template --exclude=~/Documents/Alteeve/SimEngine/Git\ Code/enginecore/simengine-cli
}