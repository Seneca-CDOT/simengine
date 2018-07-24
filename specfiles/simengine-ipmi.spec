Name:      simengine-ipmi
Version:   1
Release:   1
Summary:   SimEngine - IPMI Emulator Plugin
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

Requires: simengine-cli, OpenIPMI, OpenIPMI-lanserv, OpenIPMI-devel, gcc

%description
Compiles and installs the OpenIPMI plugin for use with SimEngine.

%prep
%autosetup -c %{name}

%build
gcc -shared -o %{_bindir}/%{name}/haos_extend.so -fPIC %{_datadir}/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_datadir}/%{name}/
cp -fRp ipmi_sim %{buildroot}%{_datadir}/%{name}/
cp -fRp ipmi_template %{buildroot}%{_datadir}/%{name}/

%files
%{_datadir}/%{name}/ipmi_sim
%{_datadir}/%{name}/ipmi_template

%changelog
* Tue Jul 24 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file