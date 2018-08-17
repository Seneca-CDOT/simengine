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
 
BuildRequires:  python2-devel
BuildRequires:  python2dist(mock)
BuildRequires:  python2dist(pytest) >= 2.5.0
BuildRequires:  python2dist(setuptools)

%description
The Python interface to the Redis key-value store. Installation redis-py
requires a running Redis server. See Redis's quickstart < for installation
instructions.To install redis-py, simply:.. code-block:: bash $ sudo pip
install redisor alternatively (you really should be using pip though):.. code-
block:: bash $ sudo easy_install redisor from source:.. code-block:: bash $
sudo python setup.py install

%package -n     python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}

%description -n python2-%{pypi_name}
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
%py2_build

%install
%py2_install

%check
%{__python2} setup.py test

%files -n python2-%{pypi_name}
%license LICENSE
%doc README.rst
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 2.10.6-1
- Initial package.
