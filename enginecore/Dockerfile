FROM fedora:29

# RUN dnf upgrade -y

# install simengine-dnf packages
# RUN dnf install libvirt OpenIPMI OpenIPMI-lanserv OpenIPMI-libs OpenIPMI-devel python3-libvirt gcc redis ipmitool -y

# install neo4j
RUN cd /tmp
RUN dnf install wget -y
RUN /usr/bin/wget http://debian.neo4j.org/neotechnology.gpg.key
RUN rpm --import neotechnology.gpg.key
RUN echo $'[neo4j] \n\
name=Neo4j RPM Repository\n\
baseurl=https://yum.neo4j.org/stable \n\
enabled=1 \n\
gpgcheck=1 \n\
[neo4j]' >> /etc/yum.repos.d/neo4j.repo

RUN cat /etc/yum.repos.d/neo4j.repo
RUN dnf install neo4j -y

WORKDIR /usr/src/app
COPY . .

LABEL  com.circleci.preserve-entrypoint=true
ENTRYPOINT contacts