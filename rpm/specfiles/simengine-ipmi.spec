Name:      simengine-ipmi
Version:   1
Release:   1
Summary:   SimEngine - IPMI Emulator Plugin
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: x86_64

BuildRequires: OpenIPMI-devel, gcc
Requires: simengine-database, OpenIPMI, OpenIPMI-lanserv

%description
Compiles and installs the OpenIPMI plugin for use with SimEngine.

%global debug_package %{nil}

%prep
%autosetup -c %{name}

%build
gcc -shared -o %{_builddir}/%{name}-%{version}/haos_extend.so -fPIC %{_builddir}/%{name}-%{version}/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_datarootdir}/simengine/enginecore/
mkdir -p %{buildroot}/usr/lib/simengine/
cp -fRp ipmi_sim %{buildroot}%{_datarootdir}/simengine/enginecore/
cp -fRp ipmi_template %{buildroot}%{_datarootdir}/simengine/enginecore/
cp -fp haos_extend.so %{buildroot}/usr/lib/simengine/

%files
%{_datarootdir}/simengine/enginecore/ipmi_sim
%{_datarootdir}/simengine/enginecore/ipmi_template
/usr/lib/simengine/haos_extend.so


%changelog
* Tue Jul 24 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file