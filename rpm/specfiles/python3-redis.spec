# Created by pyp2rpm-3.3.2
%global pypi_name redis

Name:           python-%{pypi_name}
Version:        2.10.6
Release:        1%{?dist}
Summary:        Python client for Redis key-value store

License:        MIT
URL:            http://github.com/andymccurdy/redis-py
Source0:        https://files.pythonhosted.org/packages/source/r/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python3-devel
BuildRequires:  python3dist(mock)
BuildRequires:  python3dist(pytest) >= 2.5.0
BuildRequires:  python3dist(setuptools)

%description
The Python interface to the Redis key-value store. Installation redis-py
requires a running Redis server. See Redis's quickstart < for installation
instructions.To install redis-py, simply:.. code-block:: bash $ sudo pip
install redisor alternatively (you really should be using pip though):.. code-
block:: bash $ sudo easy_install redisor from source:.. code-block:: bash $
sudo python setup.py install

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

%description -n python3-%{pypi_name}
The Python interface to the Redis key-value store. Installation redis-py
requires a running Redis server. See Redis's quickstart < for installation
instructions.To install redis-py, simply:.. code-block:: bash $ sudo pip
install redisor alternatively (you really should be using pip though):.. code-
block:: bash $ sudo easy_install redisor from source:.. code-block:: bash $
sudo python setup.py install


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install

%check
%{__python3} setup.py test

%files -n python3-%{pypi_name}
%license LICENSE
%doc README.rst
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 2.10.6-1
- Initial package.
