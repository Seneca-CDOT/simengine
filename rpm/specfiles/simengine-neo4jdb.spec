Name:      simengine-neo4jdb
Version:   1
Release:   1
Summary:   SimEngine - Neo4j Database
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

Requires:  neo4j, python3-libvirt

%description
Installs the SimEngine database configuration for Neo4j.

%pre
systemctl stop neo4j

%prep
%autosetup -c %{name}

%install
mkdir -p %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
cp -fp auth %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/

%files
%attr(0644, neo4j, neo4j) %{_sharedstatedir}/neo4j/data/dbms/auth

%post
systemctl enable neo4j --now
wait 10
echo "CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;" | cypher-shell -u simengine -p simengine

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- First alpha flight