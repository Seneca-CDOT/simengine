Name:      simengine-dashboard
Version:   3.7
Release:   3
Summary:   SimEngine - Dashboard
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global gittag %{version}

Source0:   https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz

Requires: simengine-database, simengine-core, httpd

%description
Dashboard front-end website files for SimEngine.

%global debug_package %{nil}

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_localstatedir}/www/html/
cd simengine-%{version}/dashboard/prebuild
#cp -fRp images %{buildroot}%{_localstatedir}/www/html/
#cp -fp vendors.js %{buildroot}%{_localstatedir}/www/html/
#cp -fp main.js %{buildroot}%{_localstatedir}/www/html/
#cp -fp main.css %{buildroot}%{_localstatedir}/www/html/
#cp -fp vendors.css %{buildroot}%{_localstatedir}/www/html/
#cp -fp vendors.js.map %{buildroot}%{_localstatedir}/www/html/
#cp -fp vendors.css.map %{buildroot}%{_localstatedir}/www/html/
#cp -fp main.js.map %{buildroot}%{_localstatedir}/www/html/
#cp -fp main.css.map %{buildroot}%{_localstatedir}/www/html/
#cp -fp favicon.ico %{buildroot}%{_localstatedir}/www/html/
#cp -fp index.html %{buildroot}%{_localstatedir}/www/html/
cp -fpr * %{buildroot}%{_localstatedir}/www/html

%files
%{_localstatedir}/www/html/images
%{_localstatedir}/www/html/vendors.js
%{_localstatedir}/www/html/main.js
%{_localstatedir}/www/html/main.css
%{_localstatedir}/www/html/vendors.css
%{_localstatedir}/www/html/vendors.js.map
%{_localstatedir}/www/html/vendors.css.map
%{_localstatedir}/www/html/main.js.map
%{_localstatedir}/www/html/main.css.map
%{_localstatedir}/www/html/favicon.ico
%{_localstatedir}/www/html/index.html

%post
systemctl enable httpd.service --now

%changelog
* Fri Mar 01 2019 Chris Tyler <chris.tyler@senecacollege.ca> - 3.7-3
- Updated for simengine 3.7

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file
