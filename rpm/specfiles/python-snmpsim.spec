# Created by pyp2rpm-3.3.2
%global pypi_name snmpsim

Name:           python-%{pypi_name}
Version:        0.4.7
Release:        3%{?dist}
Summary:        SNMP Agents simulator

License:        BSD
URL:            https://github.com/etingof/snmpsim
Source0:        https://files.pythonhosted.org/packages/source/s/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
Patch0:         0001-snmpsim-fix-cache-permissions.patch
Patch1:         0002-snmpsim-fix-redis-returns.patch
Patch2:         0003-snmpsim-fix-v1walk-crash.patch

BuildArch:      noarch
 
BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(sphinx)

%description
SNMP Simulator is a tool that acts as multitude of SNMP Agents built into real
physical devices, from SNMP Manager's point of view. Simulator builds and uses
a database of physical devices' SNMP footprints to respond like their original
counterparts do.

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}
 
Requires:       python3dist(pysnmp) < 5.0.0
Requires:       python3dist(pysnmp) >= 4.4.12
Requires:       python3dist(pyasn1)

%description -n python3-%{pypi_name}
SNMP Simulator is a tool that acts as multitude of SNMP Agents built into real
physical devices, from SNMP Manager's point of view. Simulator builds and uses
a database of physical devices' SNMP footprints to respond like their original
counterparts do.

%package -n python-%{pypi_name}-doc
Summary:        snmpsim documentation
%description -n python-%{pypi_name}-doc
Documentation for snmpsim

%prep
%autosetup -p1 -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
echo "%{_prefix}"

%build
%py3_build
# generate html docs 
PYTHONPATH=${PWD} sphinx-build-3 docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%{__python3} %{py_setup} %{?py_setup_args} install --prefix=/usr -O1 --skip-build --root %{buildroot} %{?*}
exit 0

%files -n python3-%{pypi_name}
%license LICENSE.txt docs/source/license.rst
/usr/snmpsim
%{python3_sitelib}
%{_bindir}/datafile.py
%{_bindir}/mib2dev.py
%{_bindir}/pcap2dev.py
%{_bindir}/snmprec.py
%{_bindir}/snmpsimd.py
%files -n python-%{pypi_name}-doc
%doc html
%license LICENSE.txt docs/source/license.rst


%changelog
* Fri Aug 20 2021 Tsu-ba-me <ynho.li.aa.e@gmail.com> - 0.4.7-3
- Revise all patches and extend to build on CentOS 8 Stream.

* Thu Nov 12 2020 Brian Sawa <noahpop77@gmail.com> - 0.4.7-2
- Updated daemon.py to allow it to be executed with superuser.

* Mon Oct 05 2020 bsawa - 0.4.7-1
- Initial package.
