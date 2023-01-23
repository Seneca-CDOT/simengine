Name:           simengine-repo
Version:        3.42
Release:        1%{?dist}
Summary:        SimEngine - Repo
BuildArch:	noarch

License:        GPLv3+
URL:            https://github.com/Seneca-CDOT/simengine

Source0: simengine.repo

%description
Package to install simengine repo file 

%install
install -d %{buildroot}/%{_sysconfdir}/yum.repos.d
install -p %{SOURCE0} %{buildroot}/%{_sysconfdir}/yum.repos.d/simengine.repo

%files
%{_sysconfdir}/yum.repos.d/simengine.repo


%changelog

* Sat Jan 21 2023 Tanner Moss <tmoss404@gmail.com>
- Initial packaging

