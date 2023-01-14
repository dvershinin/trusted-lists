# trusted-lists

IP sets for external services typically whitelisted on a web server (payment providers, etc.)

Generate .txt for IP sets of:

* [Stripe Webhooks](https://stripe.com/files/ips/ips_webhooks.txt) 
* [PayPal IPN](https://www.paypal.com/mn/smarthelp/article/what-are-the-ip-addresses-for-live-paypal-servers-ts1056)

Consumable by FirewallD / fds / NGINX.

## Package naming

* `firewalld-ipset-<name>` for FirewallD IP sets
* 

Deliver as noarch RPM package for easy updating on CentOS/RHEL-like systems.

Optimize ipsets with https://github.com/firehol/iprange/wiki

Installs to /usr/share/trusted-lists/plain/<name>.txt and
/usr/share/trusted-lists/nginx/<name>.conf
and one major list of trusted called trusted-lists

## Future

This project is to be complemented by another, e.g. [server-lists](https://github.com/dvershinin/server-lists).
The idea is that you reduce bot traffic by blocking all remote servers in server-lists project, while whitelisting the ones from trusted-lists.
