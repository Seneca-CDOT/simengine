Name:           simengine-demo
Version:        3.41
Release:        1%{?dist}
Summary:        SimEngine - Demo

%global gittag %{version}
%global selected_libdir /usr/lib64

License:        GPLv3+
URL:            https://github.com/Seneca-CDOT/simengine
Source0:        https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz
  
Requires:       virsh
Requires:	zenity
Requires:	polkit

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
* Thu Jan 19 2023 Chris Tyler <chris@tylers.info> - 3.41-1
- new version

* Mon Jan 16 2023 Tanner Moss <tmoss404@gmail.com>
- 
