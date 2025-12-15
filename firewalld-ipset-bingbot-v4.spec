%global ipset_name bingbot-v4

Name:           firewalld-ipset-%{ipset_name}
Version:        20251215
Release:        1%{?dist}
Summary:        Microsoft Bing crawler IP ranges
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://www.bing.com/toolbox/bingbot.json
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Microsoft Bing crawler IP ranges

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
