Name:           simengine-demo
Version:        0.01
Release:        1%{?dist}
Summary:        SimEngine - Demo

License:        GPLv3+
URL:            https://github.com/Seneca-CDOT/simengine
Source0:        https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz
  
Requires:       

%description
Files for downloading, installing, and running a prepared Simengine VM for use in demoing Simengine and Alteeve Anvil dashboards.

%prep
%autosetup

%install
rm -rf $RPM_BUILD_ROOT
%make_install


%files
%license add-license-file-here
%doc add-docs-here



%changelog
* Mon Jan 16 2023 Tanner Moss <tmoss404@gmail.com>
- 
