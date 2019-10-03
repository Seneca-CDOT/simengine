# Created by pyp2rpm-3.3.2
%global pypi_name pysnmp

Name:           python-%{pypi_name}
Version:        4.4.12
Release:        1%{?dist}
Summary:        SNMP library for Python

License:        BSD
URL:            https://github.com/etingof/pysnmp
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python2dist(setuptools)
BuildRequires:  python2dist(sphinx)

%description
SNMP v1/v2c/v3 engine and Standard Applications suite written in pure-Python.
Supports Manager/Agent/Proxy roles, Manager/Agent-side MIBs, asynchronous
operation and multiple network transports.

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       python2dist(pyasn1) >= 0.2.3
Requires:       python2dist(pycryptodomex)
Requires:       python2dist(pysmi)
%description -n python2-%{pypi_name}
SNMP v1/v2c/v3 engine and Standard Applications suite written in pure-Python.
Supports Manager/Agent/Proxy roles, Manager/Agent-side MIBs, asynchronous
operation and multiple network transports.

%package -n python-%{pypi_name}-doc
Summary:        pysnmp documentation
%description -n python-%{pypi_name}-doc
Documentation for pysnmp

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

%files -n python2-%{pypi_name}
%license LICENSE.rst docs/source/license.rst
%doc README.md
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python-%{pypi_name}-doc
%doc html
%license LICENSE.rst docs/source/license.rst

%changelog
* Thu Oct 03 2019 Chris Tyler <ctyler.fedora@gmail.com> - 4.4.12-1
- Initial package.
