# Created by pyp2rpm-3.3.2
%global pypi_name pysmi

Name:           python-%{pypi_name}
Version:        0.3.4
Release:        2%{?dist}
Summary:        SNMP SMI/MIB Parser

License:        BSD
URL:            https://github.com/etingof/pysmi
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python2dist(ply)
BuildRequires:  python2dist(setuptools)
BuildRequires:  python3dist(sphinx)

%description
A pure-Python implementation of SNMP/SMI MIB parsing and conversion library.

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       python2dist(ply)
%description -n python2-%{pypi_name}
A pure-Python implementation of SNMP/SMI MIB parsing and conversion library.

%package -n python-%{pypi_name}-doc
Summary:        pysmi documentation
%description -n python-%{pypi_name}-doc
Documentation for pysmi

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build
# generate html docs 
PYTHONPATH=${PWD} sphinx-build docs/source html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%py2_install

%check
%{__python2} setup.py test

%files -n python2-%{pypi_name}
%license LICENSE.rst docs/source/license.rst
%doc README.md docs/README.txt
%{_bindir}/mibcopy.py
%{_bindir}/mibdump.py
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python-%{pypi_name}-doc
%doc html
%license LICENSE.rst docs/source/license.rst

%changelog
* Thu Jul 30 2020 Chris Tyler <chris@tylers.info> - 0.3.4-2
- Adjustments for f32+python2

* Thu Oct 03 2019 Chris Tyler <ctyler.fedora@gmail.com> - 0.3.4-1
- Initial package.
