Name:           simengine-demo
Version:        3.42
Release:        1%{?dist}
Summary:        SimEngine - Demo
BuildArch:	noarch

%global gittag %{version}
%global selected_libdir /usr/lib64

License:        GPLv3+
URL:            https://github.com/Seneca-CDOT/simengine
Source0:        https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz
  
Requires:       libvirt-client
Requires:	zenity
Requires:	polkit

%description
Files for downloading, installing, and running a prepared Simengine VM for use in demoing Simengine and Alteeve Anvil dashboards.

%prep
%autosetup -n simengine-%{version}

%install
install -d %{buildroot}/%{_datadir}/applications
install -p demo/simengine-demo.desktop %{buildroot}/%{_datadir}/applications/
install -d %{buildroot}/%{_datadir}/polkit-1/actions/
install -p demo/org.freedesktop.policykit.simengine-demo.policy %{buildroot}/%{_datadir}/polkit-1/actions/
install -d %{buildroot}/%{_bindir}
install -p demo/simengine-demo %{buildroot}/%{_bindir}


%files
%license LICENSE.txt
%{_bindir}/*
%{_datadir}/applications/*
%{_datadir}/polkit-1/actions/*


%changelog
* Fri Jan 20 2023 Chris Tyler <chris@tylers.info> - 3.42-1
- new version

* Thu Jan 19 2023 Chris Tyler <chris@tylers.info> - 3.41-2
- dependency fixes

* Thu Jan 19 2023 Chris Tyler <chris@tylers.info> - 3.41-1
- new version

* Mon Jan 16 2023 Tanner Moss <tmoss404@gmail.com>
- Initial packaging
