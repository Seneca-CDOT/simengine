# The base image for circleci
FROM fedora:29 as upgrade

# install simengine-dnf packages
RUN dnf upgrade -y


FROM upgrade as add_repo

RUN dnf install gzip ca-certificates openssh-server git libvirt libvirt-devel redhat-rpm-config OpenIPMI OpenIPMI-lanserv \
    OpenIPMI-libs OpenIPMI-devel python3-libvirt gcc redis ipmitool python3-devel python2-devel net-snmp-utils -y
RUN dnf clean all -y
RUN python3 -m pip install --upgrade pip
RUN python2 -m pip install --upgrade pip


# install neo4j
RUN cd /tmp
RUN dnf install wget -y
RUN /usr/bin/wget http://debian.neo4j.org/neotechnology.gpg.key
RUN ls -l
RUN rpm --import neotechnology.gpg.key
RUN echo $'[neo4j]\nname=Neo4j RPM Repository\nbaseurl=https://yum.neo4j.org/stable\nenabled=1\ngpgcheck=1\n[neo4j]' >> /etc/yum.repos.d/neo4j.repo


FROM add_repo as install

RUN dnf install neo4j -y
RUN neo4j start
RUN sleep 5
RUN neo4j status
RUN echo "CALL dbms.changePassword('neo4j-simengine'); CALL dbms.security.createUser('simengine', 'simengine', false);"| cypher-shell -u neo4j -p neo4j \
RUN dnf clean all -y

# simengine installation:

WORKDIR /usr/src/app

LABEL com.circleci.preserve-entrypoint=true
