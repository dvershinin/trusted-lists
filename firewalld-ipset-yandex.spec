%global ipset_name yandex

Name:           firewalld-ipset-%{ipset_name}
Version:        
Release:        1%{?dist}
Summary:        Yandex Search crawler IP ranges
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://yandex.com/ips
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Yandex Search crawler IP ranges

%prep
# nothing to do


%build
# https://firewalld.org/documentation/man-pages/firewalld.ipset.html


%install
%{__mkdir} -p $RPM_BUILD_ROOT%{_usr}/lib/firewalld/ipsets
%{__install} -m 644 -p %{SOURCE0} \
    $RPM_BUILD_ROOT%{_usr}/lib/firewalld/ipsets/%{ipset_name}.xml


%files
%{_usr}/lib/firewalld/ipsets/%{ipset_name}.xml


%post
test -f /usr/bin/firewall-cmd && firewall-cmd --reload --quiet || :


%changelog
# no changelog
