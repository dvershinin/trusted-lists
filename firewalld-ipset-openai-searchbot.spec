%global ipset_name openai-searchbot

Name:           firewalld-ipset-%{ipset_name}
Version:        20251018
Release:        1%{?dist}
Summary:        OpenAI SearchBot FirewallD IP set
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://openai.com/searchbot.json
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Outbound IP ranges used by OpenAI SearchBot, which retrieves content for search-index related features.
Source: openai.com/searchbot.json (JSON: prefixes[].ipv4Prefix)


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
