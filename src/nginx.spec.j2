Name: nginx-cloudflare-ips-v4
Version: 20190405
Release: 3%{?dist}
Summary: Cloudflare IPv4 list for NGINX
Source0: realip-from-ipv4.conf
License: BSD
Requires: nginx
BuildArch: noarch
# List the arches that the dependent package builds on below
ExclusiveArch: x86_64 noarch
URL: https://www.getpagespeed.com/server-setup/nginx/cloudflare-and-nginx-automatic-sync-of-cloudflare-trusted-ip-addresses

%description
Cloudflare IPv4 list for NGINX

%install
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/nginx/cloudflare
%{__install} -m 644 -p %{SOURCE0} \
    $RPM_BUILD_ROOT%{_sysconfdir}/nginx/cloudflare/realip-from-ipv4.conf

%files
%config(noreplace) /etc/nginx/cloudflare/realip-from-ipv4.conf

%postun
if [ $1 -ge 1 ]; then
    /sbin/service nginx status  >/dev/null 2>&1 || exit 0
    /sbin/service nginx reload  >/dev/null 2>&1 || echo 0
fi

%changelog
* Sat May 11 2019 Danila Vershinin <info@getpagespeed.com> 20190405-3
- auto-reload nginx upon update


* Fri Apr 05 2019 Danila Vershinin <info@getpagespeed.com> 20190405-2
- upstream version auto-updated to 20190405