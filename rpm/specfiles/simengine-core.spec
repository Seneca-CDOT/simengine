Name:      simengine-core
Version:   1
Release:   1
Summary:   SimEngine - Core
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

#Requires: simengine-database, python-pysnmp, python-circuits, python-snmpsim, python3-libvirt
Requires: simengine-database, simengine-cli, simengine-ipmi, python3-libvirt

%description
Core files for SimEngine.

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_datarootdir}/simengine/enginecore/script/
mkdir -p %{buildroot}%{_prefix}/lib/systemd/system/
cp -fRp data %{buildroot}%{_datarootdir}/simengine/
cp -fRp enginecore %{buildroot}%{_datarootdir}/simengine/enginecore/
cp -fp snmppub.lua %{buildroot}%{_datarootdir}/simengine/enginecore/script/
cp -fp app.py %{buildroot}%{_datarootdir}/simengine/enginecore/
cp -fp simengine-core.service %{buildroot}%{_prefix}/lib/systemd/system/
exit 0

%files
%{_datarootdir}/simengine/data
%{_datarootdir}/simengine/enginecore/script/snmppub.lua
%{_datarootdir}/simengine/enginecore/app.py
%{_datarootdir}/simengine/enginecore/enginecore
%attr(0644, root, root) %{_prefix}/lib/systemd/system/simengine-core.service

%post
systemctl daemon-reload
systemctl enable simengine-core.service --now

%changelog
* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file