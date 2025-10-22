%global ipset_name stripe

Name:           firewalld-ipset-%{ipset_name}
Version:        20251022
Release:        1%{?dist}
Summary:        Stripe FirewallD IP set
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://stripe.com/files/ips/ips_webhooks.txt
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Stripe FirewallD IP set

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