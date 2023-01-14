# trusted-lists

IP sets for external services typically whitelisted on a web server (payment providers, etc.)
Consumable by FirewallD/[fds](https://fds.getpagespeed.com/)/NGINX (planned).
Delivered as *noarch* RPM packages for easy updating on CentOS/RHEL-like systems. 

## Usage

### Example. Trusting PayPal Webhook IP addresses

Install the PayPal IP set:

```console
dnf -y install https://extras.getpagespeed.com/release-latest.rpm
dnf -y install firewalld-ipset-paypal
```

Now, FirewallD knows about the new IP set named `paypal`. 
It will appear in the list of known IP sets provided by `firewall-cmd --get-ipsets` output.

Trust it like so:

```console
firewall-cmd --permanent --zone=trusted --add-source=ipset:paypal
firewall-cmd --reload
```

You can set the respective package `firewalld-ipset-paypal` to automatically update via `dnf`
in order to ensure trust of updated PayPal IP addresses.

## Available IP set packages

* `firewalld-ipset-twitter`
* `firewalld-ipset-stripe` - [Stripe Webhooks](https://stripe.com/files/ips/ips_webhooks.txt) 
* `firewalld-ipset-paypal` - [PayPal IPN](https://www.paypal.com/mn/smarthelp/article/what-are-the-ip-addresses-for-live-paypal-servers-ts1056)
* `firewalld-ipset-metabase`
* `firewalld-ipset-cloudflare-v6`
* `firewalld-ipset-cloudflare-v4`
* `firewalld-ipset-circleci`
* `firewalld-ipset-braintree`

## Package naming

* `firewalld-ipset-<name>` for FirewallD IP sets
* (Planned) `nginx-whitelist-<name>` for NGINX conf file with `allow` directives

## TODO

* Optimize IP sets with https://github.com/firehol/iprange/wiki
* Install to `/usr/share/trusted-lists/plain/<name>.txt` and `/usr/share/trusted-lists/nginx/<name>.conf`

## Future

This project is to be complemented by another, e.g. [server-lists](https://github.com/dvershinin/server-lists).
The idea is that you reduce bot traffic by blocking all remote servers in `server-lists` project, while whitelisting the ones from `trusted-lists`.
