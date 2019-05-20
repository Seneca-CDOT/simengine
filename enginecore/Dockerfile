FROM fedora:29


# install simengine-dnf packages
RUN dnf upgrade -y \
    && dnf install gzip ca-certificates openssh-server git libvirt libvirt-devel redhat-rpm-config OpenIPMI OpenIPMI-lanserv \
    OpenIPMI-libs OpenIPMI-devel python3-libvirt gcc redis ipmitool python3-devel python2-devel -y \
    && dnf clean all -y \
    && python3 -m pip install --upgrade pip \
    && python2 -m pip install --upgrade pip

# install neo4j
RUN cd /tmp \
    && dnf install wget -y \
    && /usr/bin/wget http://debian.neo4j.org/neotechnology.gpg.key \
    && ls -l \
    && rpm --import neotechnology.gpg.key \
    && echo $'[neo4j]\nname=Neo4j RPM Repository\nbaseurl=https://yum.neo4j.org/stable\nenabled=1\ngpgcheck=1\n[neo4j]' >> /etc/yum.repos.d/neo4j.repo \
    && dnf install neo4j -y \
    && neo4j start \
    && sleep 5 \
    && neo4j status \
    && echo "CALL dbms.changePassword('neo4j-simengine'); CALL dbms.security.createUser('simengine', 'simengine', false);"| cypher-shell -u neo4j -p neo4j \
    && dnf clean all -y

# simengine installation:

WORKDIR /usr/src/app

LABEL com.circleci.preserve-entrypoint=true

# COPY . .

# install plugin library
# RUN mkdir /usr/lib64/simengine \
#     && gcc -shared -o /usr/lib64/simengine/haos_extend.so -fPIC ./ipmi_sim/haos_extend.c

# install simengine pip packages
# RUN python3 -m pip install --upgrade pip \
#     && python3 -m pip install -r ./requirements.txt \
#     && python3 -m pip install -r ./dev-requirements.txt \
#     && python2 -m pip install --upgrade pip \
#     && python2 -m pip install snmpsim

# ENTRYPOINT neo4j start && sleep 5 && neo4j status && python3 -m venv venv && . venv/bin/activate && ls -l venv
# python3 -m venv venv && . venv/bin/activate