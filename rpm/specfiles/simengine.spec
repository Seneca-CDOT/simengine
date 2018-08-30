Name:      simengine
Version:   2
Release:   2
Summary:   SimEngine
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global gittag 2

Source0: https://github.com/Seneca-CDOT/%{name}/archive/%{gittag}/%{name}-%{version}.tar.gz  

BuildRequires: OpenIPMI-devel, gcc
Requires: neo4j, cypher-shell, redis, python-neo4j-driver, python-redis, python3-libvirt, OpenIPMI, OpenIPMI-lanserv, python3-redis, python2-redis, python3-pysnmp, python3-neo4j-driver, httpd

%description
Core files for SimEngine.

%global debug_package %{nil}

%pre
systemctl stop neo4j
pip3 install circuits

%prep
%autosetup -n %{name}-%{version}

%build
gcc -shared -o %{_builddir}/%{name}-%{version}/haos_extend.so -fPIC %{_builddir}/%{name}-%{version}/enginecore/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
mkdir -p %{buildroot}%{_datadir}/%{name}/
mkdir -p %{buildroot}/usr/lib/%{name}/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}%{_bindir}/
mkdir -p %{buildroot}%{_var}/www/html/%{name}/
cp -fRp dashboard/prebuild/* %{buildroot}%{_var}/www/html/%{name}/
cp -fp database/auth %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
cp -fp haos_extend.so %{buildroot}/usr/lib/%{name}/
cp -fRp enginecore %{buildroot}%{_datadir}/%{name}/
cp -fRp data %{buildroot}%{_datadir}/%{name}/
cp -fp services/simengine-core.service %{buildroot}/usr/lib/systemd/system/
ln -s /usr/share/%{name}/enginecore/simengine-cli %{buildroot}%{_bindir}/simengine-cli
exit 0

%files
%attr(0644, neo4j, neo4j) %{_sharedstatedir}/neo4j/data/dbms/auth
/usr/lib/%{name}/haos_extend.so
%{_datadir}/%{name}/enginecore
%{_datadir}/%{name}/data
/usr/lib/systemd/system/simengine-core.service
%{_bindir}/simengine-cli
%{_var}/www/html/%{name}/

%post
systemctl daemon-reload
systemctl enable neo4j --now
systemctl enable redis --now
sleep 10
echo "CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;" | cypher-shell -u simengine -p simengine
systemctl enable simengine-core.service --now

%changelog
* Thu Aug 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Converted paths to macros where applicable
- Changed source to GitHub URL using gittag release version

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file