# Created by pyp2rpm-3.3.2
%global pypi_name circuits

Name:           python-%{pypi_name}
Version:        3.2
Release:        1%{?dist}
Summary:        Asynchronous Component based Event Application Framework

License:        MIT
URL:            http://circuitsframework.com/
Source0:        https://files.pythonhosted.org/packages/source/c/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python2dist(setuptools)
BuildRequires:  python2dist(setuptools-scm)

%description
.. _Python Programming Language: .. _circuits IRC Channel: .. _FreeNode IRC
Network: .. _Python Standard Library: .. _MIT License: .. _Create an Issue: ..
_Mailing List: .. _Website: .. _PyPi: .. _Documentation: .. _Downloads:

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       python2dist(setuptools)
%description -n python2-%{pypi_name}
.. _Python Programming Language: .. _circuits IRC Channel: .. _FreeNode IRC
Network: .. _Python Standard Library: .. _MIT License: .. _Create an Issue: ..
_Mailing List: .. _Website: .. _PyPi: .. _Documentation: .. _Downloads:


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build

%install
%py2_install

%check
%{__python2} setup.py test

%files -n python2-%{pypi_name}
%license LICENSE
%doc README.rst
%{_bindir}/circuits.bench
%{_bindir}/circuits.web
%{_bindir}/htpasswd
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Tue Jul 24 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 3.2-1
- Initial package.
