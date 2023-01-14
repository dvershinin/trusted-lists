%global ipset_name paypal

Name:           firewalld-ipset-%{ipset_name}
Version:        20230114
Release:        3%{?dist}
Summary:        Braintree FirewallD IP set
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://www.paypal.com/smarthelp/article-content?article_id=TS1056&isPCC=false&isHomePage=false
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Built-in FirewallD IP set for the Braintree payment gateway.

%prep
# nothing to do


%build
# https://firewalld.org/documentation/man-pages/firewalld.ipset.html


%install
%{__mkdir} -p $RPM_BUILD_ROOT%{_usr}/lib/firewalld/ipsets
%{__install} -m 644 -p %{ipset_name}.xml \
    $RPM_BUILD_ROOT%{_usr}/lib/firewalld/ipsets/%{ipset_name}.xml


%files
%config %{_usr}/lib/firewalld/ipsets/%{ipset_name}.xml


%post
test -f /usr/bin/firewall-cmd && firewall-cmd --reload --quiet || :


%changelog
# no changelog
