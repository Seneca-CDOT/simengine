# Created by pyp2rpm-3.3.2
%global pypi_name snmpsim

Name:           python-%{pypi_name}
Version:        0.4.4
Release:        2%{?dist}
Summary:        SNMP Agents simulator

License:        BSD
URL:            https://github.com/etingof/snmpsim
Source0:        https://files.pythonhosted.org/packages/source/s/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python2dist(setuptools)
BuildRequires:  python2dist(sphinx)

%description
SNMP Simulator is a tool that acts as multitude of SNMP Agents built into real
physical devices, from SNMP Manager's point of view. Simulator builds and uses
a database of physical devices' SNMP footprints to respond like their original
counterparts do.

%global debug_package %{nil}

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       python2dist(pysnmp) >= 4.4.3
%description -n python2-%{pypi_name}
SNMP Simulator is a tool that acts as multitude of SNMP Agents built into real
physical devices, from SNMP Manager's point of view. Simulator builds and uses
a database of physical devices' SNMP footprints to respond like their original
counterparts do.

%package -n python-%{pypi_name}-doc
Summary:        snmpsim documentation
%description -n python-%{pypi_name}-doc
Documentation for snmpsim

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build
# generate html docs 
PYTHONPATH=${PWD} sphinx-build-2 docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%py2_install
exit 0

%files -n python2-%{pypi_name}
%license docs/source/license.rst LICENSE.txt
#%doc data/README.txt data/foreignformats/README.txt data/variation/README.txt data/variation/multiplex/README.txt data/public/README-v2c.txt data/public/1.3.6.1.2.1.100.1.2.0/README-v2c.txt data/public/1.3.6.1.2.1.100.1.2.0/README-v3.txt data/public/README-v3.txt data/public/1.3.6.1.6.1.1.0/README-v2c.txt data/public/1.3.6.1.6.1.1.0/README-v3.txt data/1.3.6.1.6.1.1.0/README-v2c.txt data/1.3.6.1.6.1.1.0/README-v3.txt README.md
%{_bindir}/datafile.py
%{_bindir}/mib2dev.py
%{_bindir}/pcap2dev.py
%{_bindir}/snmprec.py
%{_bindir}/snmpsimd.py
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
/usr/snmpsim/data
/usr/snmpsim/variation

%files -n python-%{pypi_name}-doc
%doc html
%license docs/source/license.rst LICENSE.txt

%changelog
* Fri Mar 01 2019 Chris Tyler <chris.tyler@senecacollege.ca> - 0.4.4-2
- Updated for simengine 3.7

* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 0.4.4-1
- Initial package.
