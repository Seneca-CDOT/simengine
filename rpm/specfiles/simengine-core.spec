Name:      simengine-core
Version:   3.36
Release:   1%{?dist}
Summary:   SimEngine - Core
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global gittag %{version}
%global selected_libdir /usr/lib64
%global openipmi_version 2.0.28

Source0: https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz  

BuildRequires: OpenIPMI-devel = %{openipmi_version}, gcc
Requires: simengine-database, python3-libvirt, OpenIPMI = %{openipmi_version}, OpenIPMI-lanserv = %{openipmi_version}, python3-redis, python3-pysnmp, python3-neo4j-driver, python3-websocket-client

%description
Core files for SimEngine.

%global debug_package %{nil}

%pre
#pip3 install circuits

%prep
%autosetup -n simengine-%{version}

%build
gcc -shared -o %{_builddir}/simengine-%{version}/haos_extend.so -fPIC %{_builddir}/simengine-%{version}/enginecore/ipmi_sim/haos_extend.c

%install
mkdir -p %{buildroot}%{_datadir}/simengine/
mkdir -p %{buildroot}%{selected_libdir}/simengine/
mkdir -p %{buildroot}%{selected_libdir}/systemd/system/
mkdir -p %{buildroot}/usr/lib/systemd/system/  # in case selected_libdir is different
mkdir -p %{buildroot}%{_bindir}/
cp -fp haos_extend.so %{buildroot}%{selected_libdir}/simengine/
cp -fRp enginecore %{buildroot}%{_datadir}/simengine/
cp -fRp data %{buildroot}%{_datadir}/simengine/
cp -fp services/simengine-core.service %{buildroot}/usr/lib/systemd/system/
ln -s /usr/share/simengine/enginecore/simengine-cli %{buildroot}%{_bindir}/simengine-cli
mkdir -p %{buildroot}%{_localstatedir}/log/simengine
exit 0

%files
%{selected_libdir}/simengine/haos_extend.so
%{_datadir}/simengine/enginecore
%{_datadir}/simengine/data
/usr/lib/systemd/system/simengine-core.service
%{_bindir}/simengine-cli
%{_localstatedir}/log/simengine
%ghost %{_localstatedir}/log/simengine/*

%post
systemctl daemon-reload
systemctl enable simengine-core.service --now

%changelog
* Mon Dec 07 2020 Tsu-ba-me <ynho.li.aa.e@gmail.com> - 3.36-1
- new version

* Wed May 06 2020 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.33-1
- new version

* Thu Jan 23 2020 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.32-1
- new version

* Wed Jan 08 2020 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.31-1
- new version

* Mon Jan 06 2020 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.30-1
- new version

* Wed Dec 11 2019 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.29-1
- new version

* Mon Dec 02 2019 Yanhao Lei <ynho.li.aa.e@gmail.com> - 3.28-1
- new version

* Thu Oct 03 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.27-1
- new version

* Thu Aug 08 2019 Olga Belavina <ol.belavina@gmail.com> - 3.26-1
- new version

* Tue Apr 30 2019 Olga Belavina <ol.belavina@gmail.com> - 3.25-1
- new version

* Mon Apr 29 2019 Olga Belavina <ol.belavina@gmail.com> - 3.24-1
- new version

* Fri Apr 26 2019 Olga Belavina <ol.belavina@gmail.com> - 3.23-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.21-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.20-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.19-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.18-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.17-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.16-1
- new version

* Fri Mar 15 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.15-1
- new version

* Mon Mar 11 2019 Chris Tyler - 3.11-1
- new version

* Mon Mar 11 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.10-1
- new version

* Mon Mar 11 2019 Chris Tyler <ctyler.fedora@gmail.com> - 3.8-1
- new version

* Fri Mar 01 2019 Chris Tyler <chris.tyler@senecacollege.ca> - 3.7-3
- Updated for simengine 3.7

* Thu Aug 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Converted paths to macros where applicable
- Changed source to GitHub URL using gittag release version

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated dependencies

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Initial alpha test file
