Name:      simengine-cli
Version:   1
Release:   1
Summary:   SimEngine - CLI
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

Requires: simengine-core, simengine-neo4jdb, simengine-redis

%description
Command line interface for SimEngine.

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_bindir}/
cp -fp simengline-cli %{buildroot}%{_bindir}/

%files
%attr(644, root, root) %{_bindir}/simengine-cli

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file