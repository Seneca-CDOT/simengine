Name:      simengine-dashboard
Version:   1
Release:   1
Summary:   SimEngine - Dashboard
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz

Requires: simengine-database, simengine-core, httpd

%description
Dashboard front-end website files for SimEngine.

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}/var/www/html/
cp -fRp images %{buildroot}/var/www/html/
cp -fp vendors.js %{buildroot}/var/www/html/
cp -fp main.js %{buildroot}/var/www/html/
cp -fp main.css %{buildroot}/var/www/html/
cp -fp vendors.css %{buildroot}/var/www/html/
cp -fp vendors.js.map %{buildroot}/var/www/html/
cp -fp vendors.css.map %{buildroot}/var/www/html/
cp -fp main.js.map %{buildroot}/var/www/html/
cp -fp main.css.map %{buildroot}/var/www/html/
cp -fp favicon.ico %{buildroot}/var/www/html/
cp -fp index.html %{buildroot}/var/www/html/

%files
/var/www/html/images
/var/www/html/vendors.js
/var/www/html/main.js
/var/www/html/main.css
/var/www/html/vendors.css
/var/www/html/vendors.js.map
/var/www/html/vendors.css.map
/var/www/html/main.js.map
/var/www/html/main.css.map
/var/www/html/favicon.ico
/var/www/html/index.html

%post
systemctl enable httpd.service --now

%changelog
* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file