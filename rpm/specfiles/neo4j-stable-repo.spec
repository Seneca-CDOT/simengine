Name:      neo4j-stable-repo
Version:   1
Release:   1
Summary:   Neo4j Repository - Stable
URL:       https://yum.neo4j.org/stable/
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

%description
Installs files necessary for access to the Neo4j Stable Release repository.

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_sysconfdir}/pki/rpm-gpg/
mkdir -p %{buildroot}%{_sysconfdir}/yum.repos.d/
cp -fp RPM-GPG-KEY-NEO4J-STABLE %{buildroot}%{_sysconfdir}/pki/rpm-gpg/
cp -fp neo4j.repo %{buildroot}%{_sysconfdir}/yum.repos.d/

%files
%attr(644, root, root) %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-NEO4J-STABLE
%attr(644, root, root) %{_sysconfdir}/yum.repos.d/neo4j.repo

%changelog
* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file