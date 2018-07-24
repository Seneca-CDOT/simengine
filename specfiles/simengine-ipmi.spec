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
gcc -shared -o %{_bindir}/%{name}/haos_extend.so -fPIC %{_sharedstate}/simengine/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_sharedstate}/simengine/
cp -fRp ipmi_sim %{buildroot}%{_sharedstate}/simengine/
cp -fRp ipmi_template %{buildroot}%{_sharedstate}/simengine/

%files
%{_sharedstate}/simengine/ipmi_sim
%{_sharedstate}/simengine/ipmi_template

%changelog
* Tue Jul 24 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file