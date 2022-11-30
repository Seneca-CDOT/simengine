Name:      simengine-database
Version:   3.39
Release:   1%{?dist}
Summary:   SimEngine - Databases
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

%global    gittag %{version}

Source0:   https://github.com/Seneca-CDOT/simengine/archive/%{gittag}/simengine-%{version}.tar.gz
BuildArch: noarch

Requires:  neo4j
Requires:  cypher-shell
Requires:  redis
Requires:  python3-neo4j-driver
Requires:  python3-redis
Requires:  chkconfig

%description
Installs the SimEngine database configuration for Neo4j.

%pre
systemctl stop neo4j

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
cp -fp simengine-%{version}/database/auth %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/

%files
%attr(0644, neo4j, neo4j) %{_sharedstatedir}/neo4j/data/dbms/auth

%post
systemctl enable neo4j --now
systemctl enable redis --now

function cyphexec { cypher-shell -u simengine -p simengine "$1"; }

echo "Begin bolt connection test to Neo4j database."
wait_count=0
wait_count_limit=5
wait_interval=4
is_failed=
while ! cyphexec "RETURN 'test';" &>/dev/null
do
    echo "Connection attempt $(( wait_count += 1 )) out of $wait_count_limit failed."
    if [[ $wait_count < $wait_count_limit ]]
    then
        echo "Wait for $wait_interval seconds before retrying."
        sleep $wait_interval
    else
        is_failed=true
        break
    fi
done

if [[ -z $is_failed ]]
then
    echo "Connection test passed; begin executing cypher commands."
    cyphexec "CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;"
else
    echo "Connection test failed; skip all cypher commands."
fi

# According to the guidelines, all scriptlets must exit with code 0.
exit 0

%changelog
* Wed Nov 30 2022 Tanner Moss <tmoss404@gmail.com> - 3.39-1
- new version

* Mon Aug 23 2021 Tsu-ba-me <ynho.li.aa.e@gmail.com> - 3.38-1
- new version

* Fri Aug 06 2021 Tsu-ba-me <ynho.li.aa.e@gmail.com> - 3.37-1
- new version

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

* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated package dependencies, converted SPEC file to encompass all database work (previously simegine-neo4jdb)

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- First alpha flight
