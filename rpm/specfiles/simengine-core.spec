Name:      simengine-core
Version:   1
Release:   1
Summary:   SimEngine - Core
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

BuildRequires: OpenIPMI-devel, gcc
#Requires: simengine-database, python-pysnmp, python-circuits, python-snmpsim, python3-libvirt
Requires: simengine-database, python3-libvirt, OpenIPMI, OpenIPMI-lanserv

%description
Core files for SimEngine.

%global debug_package %{nil}

%prep
%autosetup -c %{name}

%build
gcc -shared -o %{_builddir}/%{name}-%{version}/haos_extend.so -fPIC %{_builddir}/%{name}-%{version}/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}/usr/share/simengine/
mkdir -p %{buildroot}/usr/lib/simengine/
mkdir -p %{buildroot}/usr/lib/systemd/system/
mkdir -p %{buildroot}/usr/bin/
cp -fp haos_extend.so %{buildroot}/usr/lib/simengine/
cp -fRp enginecore %{buildroot}/usr/share/simengine/
cp -fp services/simengine-core.service %{buildroot}/usr/lib/systemd/system/
ln -s enginecore/simengine-cli %{buildroot}/usr/bin/simengine-cli

%files
/usr/lib/simengine/haos_extend.so
/usr/share/simengine/enginecore
/usr/lib/systemd/system/simengine-core.service
/usr/bin/simengine-cli

%post
systemctl daemon-reload
systemctl enable simengine-core.service --now

%changelog
* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file