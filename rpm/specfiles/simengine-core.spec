Name:      simengine-core
Version:   1
Release:   2
Summary:   SimEngine - Core
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global commit 1950343e75fcc5b647392e0b7925052d8a1b916f
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Source0:  https://github.com/Seneca-CDOT/simengine/archive/%{commit}/simengine-%{commit}.tar.gz  

BuildRequires: OpenIPMI-devel, gcc
Requires: simengine-database, python3-libvirt, OpenIPMI, OpenIPMI-lanserv, python3-redis, python2-redis, python3-pysnmp, python3-neo4j-driver

%description
Core files for SimEngine.

%global debug_package %{nil}

%pre
pip3 install circuits

%prep
%autosetup -n simengine-%{commit}

%build
gcc -shared -o %{_builddir}/simengine-%{commit}/haos_extend.so -fPIC %{_builddir}/simengine-%{commit}/enginecore/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_datadir}/simengine/
mkdir -p %{buildroot}/usr/lib/simengine/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}%{_bindir}/
cp -fp haos_extend.so %{buildroot}/usr/lib/simengine/
cp -fRp enginecore %{buildroot}%{_datadir}/simengine/
cp -fRp data %{buildroot}%{_datadir}/simengine/
cp -fp services/simengine-core.service %{buildroot}/usr/lib/systemd/system/
ln -s /usr/share/simengine/enginecore/simengine-cli %{buildroot}%{_bindir}/simengine-cli
exit 0

%files
/usr/lib/simengine/haos_extend.so
%{_datadir}/simengine/enginecore
%{_datadir}/simengine/data
/usr/lib/systemd/system/simengine-core.service
%{_bindir}/simengine-cli

%post
systemctl daemon-reload
systemctl enable simengine-core.service --now

%changelog
* Thu Aug 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Converted paths to macros where applicable
- Changed source to GitHub URL

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file