%global ipset_name circleci

Name:           firewalld-ipset-%{ipset_name}
Version:        20251205
Release:        1%{?dist}
Summary:        Well-defined IP address ranges. Supported only on paid plans of CircleCI.
License:        BSD
Requires:       firewalld
BuildArch:      noarch
URL:            https://circleci.com/docs/ip-ranges/
Source0:        %{ipset_name}.xml
BuildRequires:  python3


%description
Well-defined IP address ranges. Supported only on paid plans of CircleCI.

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