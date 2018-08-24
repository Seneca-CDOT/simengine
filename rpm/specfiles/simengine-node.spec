Name:      simengine-dashboard
Version:   1
Release:   2
Summary:   SimEngine - Dashboard
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz

Requires: simengine-database, simengine-core, httpd
BuildRequires: nodejs-packaging

%description
Dashboard front-end website files for SimEngine.

%global debug_package %{nil}

%prep
%autosetup -c %{name}

%build
npm build:prod %{_builddir}/%{name}-%{version}/dashboard/frontend/

%install
mkdir -p %{buildroot}%{_localstatedir}/www/html/
cp -fRp dashboard/frontend/public/images %{buildroot}%{_localstatedir}/www/html/

%files
%{_localstatedir}/www/html/*

%post
systemctl enable httpd.service --now

%changelog
* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file