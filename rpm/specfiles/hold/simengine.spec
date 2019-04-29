Name:      simengine
Version:   3
Release:   2
Summary:   Hardware Simulation Engine
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global gittag 3

Source0: https://github.com/Seneca-CDOT/%{name}/archive/%{gittag}/%{name}-%{version}.tar.gz  

Requires(pre): shadow-utils
BuildRequires: OpenIPMI-devel, gcc, systemd
Requires: neo4j, cypher-shell, redis, python-neo4j-driver, python-redis, python3-libvirt, OpenIPMI, OpenIPMI-lanserv, python3-websocket-client, python3-redis, python2-redis, python3-pysnmp, python3-neo4j-driver, httpd

%description
Simengine is a hardware simulation engine that models high-availability setups.

%global debug_package %{nil}

%pre
systemctl stop neo4j
pip3 install circuits
getent group neo4j >/dev/null || groupadd -r neo4j
getent passwd neo4j >/dev/null || \
    useradd -r -g neo4j -s /sbin/nologin \
    -c "Neo4j Database Account" neo4j
exit 0

%prep
%autosetup -n %{name}-%{version}

%build
gcc -shared -o %{_builddir}/%{name}-%{version}/haos_extend.so -fPIC %{_builddir}/%{name}-%{version}/enginecore/ipmi_sim/haos_extend.c
objcopy --only-keep-debug %{_builddir}/%{name}-%{version}/haos_extend.so %{_builddir}/%{name}-%{version}/haos_extend.debug
strip --strip-debug --strip-unneeded %{_builddir}/%{name}-%{version}/haos_extend.so

%install
mkdir -p %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
mkdir -p %{buildroot}%{_datadir}/%{name}/
mkdir -p %{buildroot}%{_libdir}/%{name}/
mkdir -p %{buildroot}%{_unitdir}/
mkdir -p %{buildroot}%{_bindir}/
mkdir -p %{buildroot}%{_var}/www/html/%{name}/
cp -fRp dashboard/prebuild/* %{buildroot}%{_var}/www/html/%{name}/
cp -fp database/auth %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
cp -fp haos_extend.so %{buildroot}%{_libdir}/%{name}/
cp -fRp enginecore %{buildroot}%{_datadir}/%{name}/
cp -fRp data %{buildroot}%{_datadir}/%{name}/
cp -fp services/simengine-core.service %{buildroot}%{_unitdir}/
ln -s %{_datadir}/%{name}/enginecore/simengine-cli %{buildroot}%{_bindir}/simengine-cli
exit 0

%files
%attr(0644, neo4j, neo4j) %{_sharedstatedir}/neo4j/data/dbms/auth
%{_libdir}/%{name}/haos_extend.so
%{_datadir}/%{name}/enginecore
%{_datadir}/%{name}/data
%{_unitdir}/simengine-core.service
%{_bindir}/simengine-cli
%{_var}/www/html/%{name}/
%exclude %{_datadir}/%{name}/enginecore/.pylintrc
%exclude %{_datadir}/%{name}/enginecore/ipmi_sim/haos_extend.c
%exclude %{_datadir}/%{name}/enginecore/ipmi_sim/.gitignore

%post
systemctl daemon-reload
systemctl enable neo4j --now
systemctl enable redis --now
sleep 10
echo "CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;" | cypher-shell -u simengine -p simengine
systemctl enable simengine-core.service --now

%changelog
* Thu Aug 23 2018 Chris Johnson <chris.johnson@senecacollege.ca> 2-2
- Converted paths to macros where applicable
- Changed source to GitHub URL using gittag release version

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca> 1-2
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca> 1-1
- Initial alpha test file