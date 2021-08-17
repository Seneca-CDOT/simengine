%global srcname neotime
%global sum Nanosecond resolution temporal types
%global desc %{sum}
%global debug_package %{nil}
# Disable Python 2
%bcond_with python2
# Enable Python 3
%bcond_without python3

Name:           python-%{srcname}
Version:        1.0.0
Release:        12%{?dist}
Summary:        %{sum}

License:        ASL 2.0
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        https://files.pythonhosted.org/packages/source/n/%{srcname}/%{srcname}-%{version}.tar.gz

BuildArch:      noarch
%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
%endif
%if %{with python3}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
%endif

%description
%{desc}

%if %{with python3}
%package -n python%{python3_pkgversion}-%{srcname}
Summary:        %{sum}
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}
Requires:       python3-pytz
Requires:       python3-six

%description -n python%{python3_pkgversion}-%{srcname}
%{desc}
%endif

%if %{with python2}
%package -n python2-%{srcname}
Summary:        %{sum}
%if 0%{?fedora} || 0%{?rhel} > 7
Requires:       python2-pytz
Requires:       python2-six
%else
Requires:       pytz
Requires:       python-six
%endif
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
%{desc}
%endif


%prep
%autosetup -n %{srcname}-%{version}
find ./ -name '*.py' -exec sed -i '/^#!\/usr\/bin\/env python$/d' '{}' ';'

%build
%if %{with python2}
%py2_build
%endif
%if %{with python3}
%py3_build
%endif

%install
%if %{with python2}
%py2_install
%endif
%if %{with python3}
%py3_install
%endif

%if %{with python2}
%files -n python2-%{srcname}
%doc README.rst
%{python2_sitelib}/*
%endif

%if %{with python3}
%files -n python%{python3_pkgversion}-%{srcname}
%doc README.rst
%{python3_sitelib}/*
%endif

%changelog
* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-10
- Rebuilt for Python 3.9

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-8
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-7
- Rebuilt for Python 3.8

* Wed Jul 24 2019 mprahl <mprahl@redhat.com> - 1.0.0-6
- Clean up the specfile to match the Python guidelines

* Wed Jul 24 2019 mprahl <mprahl@redhat.com> - 1.0.0-5
- Stop building Python 2 packages for F31+

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-2
- Rebuilt for Python 3.7

* Thu Jun 07 2018 mprahl <mprahl@redhat.com> - 1.0.0-1
- Initial release
