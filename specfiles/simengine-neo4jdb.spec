Name:      simengine-neo4jdb
Version:   1
Release:   1
Summary:   SimEngine - Neo4j Database
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   
BuildArch: x86_64

Requires:  neo4j

%description

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
