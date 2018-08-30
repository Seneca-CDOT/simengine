#!/bin/bash

# Archives SimEngine source files from local Git to tarball in ~/rpmbuilds/SOURCES/

core () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-core-1.tar.gz -C ~/Documents/Alteeve/SimEngine/Git\ Code/ enginecore services data
}

frontend () {
	tar -czvf ~/rpmbuild/SOURCES/simengine-dashboard-1.tar.gz -C ~/Documents/Alteeve/SimEngine/Git\ Code/dashboard/frontend/public .
}