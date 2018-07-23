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
Installs the SimEngine database configuration for Neo4j.

%pre

%prep
autosetup -c %{name}

%install

%files

%post
systemctl enable neo4j --now

%postun

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
