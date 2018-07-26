Name:      simengine
Version:   1
Release:   1
Summary:   SimEngine - HA Hardware Simulator
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   
BuildArch: x86_64

Conflicts: firewalld
Requires:  iptables-services, nodejs, redis, neo4j, python3-libvirt, OpenIPMI, OpenIPMI-lanserv, OpenIPMI-devel, gcc

%description
Hardware simulation engine for Alteeve's Anvil! Intelligent Availability platform and similar HA configurations

%pre
systemctl enable iptables --now &> /dev/null
iptables -F

%prep
autosetup -c %{name}

%install

%files

%post

%postun

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
