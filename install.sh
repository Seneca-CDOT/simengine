#!/bin/bash

# Temporary install script.

update_fedora () {
	echo "-- Updating Fedora --"
	echo ""
	dnf -y update
	echo ""
}

replace_firewalld () {
	echo "-- Replacing Firewalld w/IPTables --"
	echo ""
	dnf -y install iptables-services
	systemctl stop firewalld
	systemctl enable iptables --now
	dnf -y remove firewalld
	iptables -F
	echo ""
}

firewall_rules () {
	echo "-- Applying Firewall Rules --"
	echo ""
	systemctl restart iptables
	iptables -I INPUT 2 -p tcp --dport 8000 -m comment --comment "SimEngine WebSocket" -j ACCEPT
	iptables -I INPUT 2 -p udp --dport 8000 -m comment --comment "SimEngine WebSocket" -j ACCEPT
	iptables -I INPUT 2 -p tcp --dport 9000 -m comment --comment "SimEngine FrontEnd" -j ACCEPT
	iptables -I INPUT 2 -p udp --dport 9000 -m comment --comment "SimEngine FrontEnd" -j ACCEPT
	/sbin/service iptables save
	echo ""
}

install_utilities () {
	echo "-- Installing Common Utilities --"
	echo ""
	dnf -y install nmap vim
	echo ""
}

install_git () {
	echo "-- Installing git --"
	echo ""
	dnf -y install git
	echo ""
}

installl_nodejs () {
	echo "-- Installing NodeJS --"
	echo ""
	dnf -y install nodejs
	echo ""
}

set_hostname () {
	echo "-- Setting Hostname --"
	echo ""
	hostnamectl set-hostname --static simengine
	hostnamectl set-hostname --transient simengine
	hostnamectl
	echo ""
}

clone_repo () {
	echo "-- Cloning SimEngine Repo Into Home --"
	echo ""
	mkdir -p /usr/share/simengine/
	chmod 755 -R /usr/share/simengine/
#	git clone https://github.com/cc452/simengine.git /usr/share/simengine/
	git clone https://github.com/Seneca-CDOT/simengine.git /usr/share/simengine/
	echo ""
}

neo4j_repoadd () {
	echo "-- Adding Neo4j Repository --"
	echo ""
	rpm --import http://debian.neo4j.org/neotechnology.gpg.key
	echo "[neo4j]" > /etc/yum.repos.d/neo4j.repo
	echo "name=Neo4j RPM Repository" >> /etc/yum.repos.d/neo4j.repo
	echo "baseurl=http://yum.neo4j.org/stable" >> /etc/yum.repos.d/neo4j.repo
	echo "enabled=1" >> /etc/yum.repos.d/neo4j.repo
	echo "gpgcheck=1" >> /etc/yum.repos.d/neo4j.repo
	cat /etc/yum.repos.d/neo4j.repo
	echo ""
}

database_install () {
	echo "-- Installing Databases --"
	echo ""
	dnf -y install redis neo4j python3-libvirt
	python3 -m pip install -r /usr/share/simengine/enginecore/requirements.txt
	pip install redis
	pip install snmpsim
	rm -rf /var/lib/neo4j/data/dbms/auth
	echo ""
}

start_db () {
	echo "-- Starting Database Daemons --"
	echo ""
	systemctl enable neo4j --now
	systemctl enable redis --now
	echo ""
}

create_dbuser () {
	echo "-- Creating SimEngine Database User --"
	echo ""
	echo "Waiting 10 seconds for Neo4j Startup..."
	sleep 10
	echo "CALL dbms.changePassword('neo4j-simengine'); CALL dbms.security.createUser('simengine', 'simengine', false);"|cypher-shell -u neo4j -p neo4j
	systemctl restart neo4j
	echo "Restarting Neo4j, please wait..."
	sleep 10
	echo ""
}

install_coredaemon () {
	echo "-- Installing and Starting SimEngine Core Daemon --"
	echo ""
	cp /usr/share/simengine/services/simengine-core.service /etc/systemd/system/simengine-core.service
	systemctl daemon-reload
	systemctl enable simengine-core --now
	echo ""
}

install_openIPMI () {
	echo "-- Instaling OpenIPMI Emulator Dependencies --"
	echo ""
	dnf -y install OpenIPMI OpenIPMI-lanserv OpenIPMI-devel gcc
	echo ""
}

build_ipmiplugin () {
	echo "-- Building IPMI Emulator Plugin --"
	echo ""
	mkdir /usr/lib/simengine/
	ln -s /usr/share/simengine/enginecore/simengine-cli.py /usr/bin/simengine-cli.py
	gcc -shared -o /usr/lib/simengine/haos_extend.so -fPIC /usr/share/simengine/enginecore/ipmi_sim/haos_extend.c
	echo ""
}

populate_db () {
	echo "-- Populating Neo4j Database --"
	echo ""
	cat /usr/share/simengine/enginecore/script/db_config.cyp | cypher-shell -u simengine -p simengine
	echo ""
}

npm_installation () {
	echo "-- Running NPM Installation --"
	echo ""
	cd /usr/share/simengine/dashboard/frontend/
	npm install
	echo ""
}

npm_start () {
	echo "-- Starting NodeJS --"
	echo ""
	cd /usr/share/simengine/dashboard/frontend/
	npm start
	echo ""
}

update_fedora
replace_firewalld
install_utilities
install_git
installl_nodejs
set_hostname
clone_repo
neo4j_repoadd
database_install
start_db
create_dbuser
install_coredaemon
install_openIPMI
build_ipmiplugin
populate_db
npm_installation
firewall_rules
npm_start