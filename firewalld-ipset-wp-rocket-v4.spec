%global ipset_name wp-rocket-v4

Name:           firewalld-ipset-%{ipset_name}
Version:        20251219
Release:        1%{?dist}
Summary:        WP Rocket cache preloading service IPv4 addresses
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://mega.wp-rocket.me/rocket-ips/rocket-ips-plain-ipv4.txt
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
WP Rocket cache preloading service IPv4 addresses

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

