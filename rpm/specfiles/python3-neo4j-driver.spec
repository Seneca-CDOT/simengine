# Created by pyp2rpm-3.3.2
%global pypi_name neo4j-driver

Name:           python-%{pypi_name}
Version:        1.6.1
Release:        2%{?dist}
Summary:        Neo4j Bolt driver for Python

License:        Apache License, Version 2.0
URL:            https://github.com/neo4j/neo4j-python-driver
Source0:        https://files.pythonhosted.org/packages/source/n/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
Patch0:         0001-neo4j-driver-fix-routing.py.patch
 
BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)

%description
**************************** Neo4j Bolt Driver for Python
****************************The Official Neo4j Driver for Python supports Neo4j
3.0 and above and Python versions 2.7, 3.4, 3.5 and 3.6. Quick Example .. code-
block:: python from neo4j.v1 import GraphDatabase driver
GraphDatabase.driver(":7687", auth("neo4j", "password")) def add_friends(tx,
name, friend_name): tx.run("MERGE (a:Person...

%global debug_package %{nil}

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}
 
Requires:       python3dist(neotime)
%description -n python3-%{pypi_name}
**************************** Neo4j Bolt Driver for Python
****************************The Official Neo4j Driver for Python supports Neo4j
3.0 and above and Python versions 2.7, 3.4, 3.5 and 3.6. Quick Example .. code-
block:: python from neo4j.v1 import GraphDatabase driver
GraphDatabase.driver(":7687", auth("neo4j", "password")) def add_friends(tx,
name, friend_name): tx.run("MERGE (a:Person...


%prep
%autosetup -p1 -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install

%files -n python3-%{pypi_name}
%doc README.rst
%{python3_sitearch}/neo4j
%{python3_sitearch}/neo4j_driver-%{version}-py?.?.egg-info

%changelog
* Thu Nov 12 2020 Brian Sawa <noahpop77@gmail.com> - 1.6.1-3
- Updated routing.py

* Fri Mar 01 2019 Chris Tyler <chris.tyler@senecacollege.ca> - 1.6.1-2
- Updated for simengine 3.7

* Fri Aug 17 2018 Chris Johnson <christopher.johnson@senecacollege.ca> - 1.6.1-1
- Initial package.
