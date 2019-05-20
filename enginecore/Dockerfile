FROM fedora:29

# RUN dnf upgrade -y

# install simengine-dnf packages
RUN dnf install gzip ca-certificates openssh-server git libvirt OpenIPMI OpenIPMI-lanserv OpenIPMI-libs OpenIPMI-devel python3-libvirt gcc redis ipmitool -y

# install neo4j
RUN cd /tmp \
    && dnf install wget -y \
    && /usr/bin/wget http://debian.neo4j.org/neotechnology.gpg.key \
    && ls -l \
    && rpm --import neotechnology.gpg.key \
    && echo $'[neo4j]\nname=Neo4j RPM Repository\nbaseurl=https://yum.neo4j.org/stable\nenabled=1\ngpgcheck=1\n[neo4j]' >> /etc/yum.repos.d/neo4j.repo \
    && dnf install neo4j -y

# install simengine python
WORKDIR /usr/src/app
COPY . .

RUN python3 -m pip install -r ./requirements.txt
RUN python3 -m pip install -r ./dev-requirements.txt
RUN python2 -m pip install snmpsim

LABEL com.circleci.preserve-entrypoint=true
ENTRYPOINT echo "hello"