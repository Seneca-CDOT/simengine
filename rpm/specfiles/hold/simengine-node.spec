Name:      simengine-dashboard
Version:   3.7
Release:   2
Summary:   SimEngine - Dashboard
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global gittag %{version}

Source0: https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz  
Source1:   http://registry.npmjs.org/babel-cli/-/babel-cli-6.26.0.tgz
Source2:   http://registry.npmjs.org/babel-core/-/babel-core-6.26.3.tgz
Source3:   http://registry.npmjs.org/babel-eslint/-/babel-eslint-8.2.3.tgz
Source4:   http://registry.npmjs.org/babel-loader/-/babel-loader-7.1.4.tgz
Source5:   http://registry.npmjs.org/babel-preset-env/-/babel-preset-env-1.7.0.tgz
Source6:   http://registry.npmjs.org/babel-preset-react/-/babel-preset-react-6.24.1.tgz
Source7:   http://registry.npmjs.org/babel-preset-stage-0/-/babel-preset-stage-0-6.24.1.tgz
Source8:   http://registry.npmjs.org/clean-webpack-plugin/-/clean-webpack-plugin-0.1.19.tgz
Source9:   http://registry.npmjs.org/css-loader/-/css-loader-0.28.11.tgz
Source10:   http://registry.npmjs.org/eslint/-/eslint-4.19.1.tgz
Source11:   http://registry.npmjs.org/eslint-loader/-/eslint-loader-2.0.0.tgz
Source12:   http://registry.npmjs.org/eslint-plugin-import/-/eslint-plugin-import-2.12.0.tgz
Source13:   http://registry.npmjs.org/eslint-plugin-react/-/eslint-plugin-react-7.8.2.tgz
Source14:   http://registry.npmjs.org/extract-text-webpack-plugin/-/extract-text-webpack-plugin-4.0.0-beta.0.tgz
Source15:   http://registry.npmjs.org/file-loader/-/file-loader-1.1.11.tgz
Source16:   http://registry.npmjs.org/html-webpack-plugin/-/html-webpack-plugin-3.2.0.tgz
Source17:   http://registry.npmjs.org/live-server/-/live-server-1.2.0.tgz
Source18:   http://registry.npmjs.org/node-sass/-/node-sass-4.9.0.tgz
Source19:   http://registry.npmjs.org/sass-loader/-/sass-loader-7.0.1.tgz
Source20:   http://registry.npmjs.org/style-loader/-/style-loader-0.21.0.tgz
Source21:   http://registry.npmjs.org/uglifyjs-webpack-plugin/-/uglifyjs-webpack-plugin-1.2.5.tgz
Source22:   http://registry.npmjs.org/url-loader/-/url-loader-1.0.1.tgz
Source23:   http://registry.npmjs.org/webpack/-/webpack-4.9.1.tgz
Source24:   http://registry.npmjs.org/webpack-bundle-analyzer/-/webpack-bundle-analyzer-2.13.1.tgz
Source25:   http://registry.npmjs.org/webpack-cli/-/webpack-cli-2.1.4.tgz
Source26:   http://registry.npmjs.org/webpack-dashboard/-/webpack-dashboard-2.0.0.tgz
Source27:   http://registry.npmjs.org/webpack-dev-server/-/webpack-dev-server-3.1.4.tgz
Source28:   http://registry.npmjs.org/webpack-merge/-/webpack-merge-4.1.2.tgz

Requires: simengine-database, simengine-core, httpd
BuildRequires: nodejs-packaging

%description
Dashboard front-end website files for SimEngine.

%global debug_package %{nil}

%prep
%autosetup -n simengine-%{version}

%build
npm build:prod %{_builddir}/%{name}-%{version}/dashboard/frontend/

%install
mkdir -p %{buildroot}%{_localstatedir}/www/html/
cp -fRp dashboard/frontend/public/images %{buildroot}%{_localstatedir}/www/html/

%{nodejs_sitelib}/<npm module name>

%files
%{_localstatedir}/www/html/*

%post
systemctl enable httpd.service --now

%changelog
* Fri Aug 24 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Modified Source0 to GitHub location

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file
