Name:      simengine-core
Version:   1
Release:   1
Summary:   SimEngine - Core
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

Requires: simengine-neo4jdb, simengine-redis

%description
Core files for SimEngine.

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_sharedstatedir}/%{name}/enginecore/script/
mkdir -p %{buildroot}%{_libdir}/systemd/system/
cp -fRp data %{buildroot}%{_sharedstatedir}/%{name}/
cp -fp snmppub.lua %{buildroot}%{_sharedstatedir}/%{name}/enginecore/script/
cp -fp app.py %{buildroot}%{_sharedstatedir}/%{name}/enginecore/
cp -fp simengine-core.service %{buildroot}%{_libdir}/systemd/system/

%files
%{_sharedstatedir}/%{name}/data
%{_sharedstatedir}/%{name}/enginecore/script/snmppub.lua
%{_sharedstatedir}/%{name}/enginecore/app.py
%attr(0644, root, root) %{_libdir}/systemd/system/simengine-core.service

%post
systemctl enable simengine-core.service --now

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file