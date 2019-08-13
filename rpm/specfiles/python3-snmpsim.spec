# Created by pyp2rpm-3.3.3
%global pypi_name snmpsim

Name:           python-%{pypi_name}
Version:        0.4.7
Release:        1%{?dist}
Summary:        SNMP Agents simulator

License:        BSD
URL:            https://github.com/etingof/snmpsim
Source0:        https://files.pythonhosted.org/packages/source/s/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
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
Requires:       python3dist(pysnmp) >= 4.4.3
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
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build
# generate html docs
PYTHONPATH=${PWD} sphinx-build-3 docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%py3_install

%files -n python3-%{pypi_name}
%license LICENSE.txt docs/source/license.rst
%doc README.md data/1.3.6.1.6.1.1.0/README-v2c.txt data/1.3.6.1.6.1.1.0/README-v3.txt data/README.txt data/foreignformats/README.txt data/public/1.3.6.1.2.1.100.1.2.0/README-v2c.txt data/public/1.3.6.1.2.1.100.1.2.0/README-v3.txt data/public/1.3.6.1.6.1.1.0/README-v2c.txt data/public/1.3.6.1.6.1.1.0/README-v3.txt data/public/README-v2c.txt data/public/README-v3.txt data/variation/README.txt data/variation/multiplex/README.txt
%{_bindir}/datafile.py
%{_bindir}/mib2dev.py
%{_bindir}/pcap2dev.py
%{_bindir}/snmprec.py
%{_bindir}/snmpsimd.py
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py%{python3_version}.egg-info
/usr/snmpsim/data
/usr/snmpsim/variation

%files -n python-%{pypi_name}-doc
%doc html
%license LICENSE.txt docs/source/license.rst

%changelog
* Tue Aug 13 2019 Olga Belavina <ol.belavina@gmail.com> - 0.4.7-1
- Initial package.
