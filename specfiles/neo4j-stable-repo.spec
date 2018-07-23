Name:      neo4j-stable-repo
Version:   1
Release:   1
Summary:   Neo4j Repository - Stable
URL:       https://yum.neo4j.org/stable/
License:   

Source0:   
BuildArch: noarch

Conflicts: 
Requires:  

%description
Installs files necessary for access to the Neo4j Stable Release repository.

%pre

%prep
autosetup -c %{name}

%install

%files

%post

%postun

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
