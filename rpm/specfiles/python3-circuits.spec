# Created by pyp2rpm-3.3.2
%global pypi_name circuits

Name:           python-%{pypi_name}
Version:        3.2
Release:        2%{?dist}
Summary:        Asynchronous Component based Event Application Framework

License:        MIT
URL:            http://circuitsframework.com/
Source0:        https://files.pythonhosted.org/packages/source/c/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
Patch0:         0001-circuits-fix-multipart.py.patch
BuildArch:      noarch
 
BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm)

%description
.. _Python Programming Language: .. _circuits IRC Channel: .. _FreeNode IRC
Network: .. _Python Standard Library: .. _MIT License: .. _Create an Issue: ..
_Mailing List: .. _Website: .. _PyPi: .. _Documentation: .. _Downloads:

%global debug_package %{nil}

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}
 
Requires:       python3dist(setuptools)
%description -n python3-%{pypi_name}
.. _Python Programming Language: .. _circuits IRC Channel: .. _FreeNode IRC
Network: .. _Python Standard Library: .. _MIT License: .. _Create an Issue: ..
_Mailing List: .. _Website: .. _PyPi: .. _Documentation: .. _Downloads:


%prep
%autosetup -p1 -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install
mv %{buildroot}%{_bindir}/htpasswd %{buildroot}%{_bindir}/htpasswd-circuits
#%check
#%{__python3} setup.py test

%files -n python3-%{pypi_name}
%license LICENSE
%doc README.rst
%{_bindir}/*
%{python3_sitelib}/*

%changelog
* Thu Nov 12 2020 Brian Sawa <noahpop77@gmail.com> - 3.2-3
- Updated to be compatible with Python 3

* Fri Mar 01 2019 Chris Tyler <chris.tyler@senecacollege.ca> - 3.2-2
- Updated for simengine 3.7

* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 3.2-1
- Initial package.
