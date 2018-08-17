# Created by pyp2rpm-3.3.2
%global pypi_name pysnmp

Name:           python-%{pypi_name}
Version:        4.4.5
Release:        1%{?dist}
Summary:        SNMP library for Python

License:        BSD
URL:            https://github.com/etingof/pysnmp
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(sphinx)

%description
SNMP v1/v2c/v3 engine and apps written in pure-Python. Supports
Manager/Agent/Proxy roles, scriptable MIBs, asynchronous operation and multiple
transports.

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}
 
Requires:       python3dist(pyasn1) >= 0.2.3
Requires:       python3dist(pycryptodomex)
Requires:       python3dist(pysmi)
%description -n python3-%{pypi_name}
SNMP v1/v2c/v3 engine and apps written in pure-Python. Supports
Manager/Agent/Proxy roles, scriptable MIBs, asynchronous operation and multiple
transports.

%package -n python-%{pypi_name}-doc
Summary:        pysnmp documentation
%description -n python-%{pypi_name}-doc
Documentation for pysnmp

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
%license docs/source/license.rst
%doc README.md
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%files -n python-%{pypi_name}-doc
%doc html
%license docs/source/license.rst

%changelog
* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 4.4.5-1
- Initial package.
