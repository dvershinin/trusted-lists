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

## Generate and build

This repo provides a generator that fetches upstream IP ranges and produces:

- plain lists in `build/<name>.txt`
- FirewallD ipset XML in `build/<name>.xml`
- packaging metadata in `build/<name>.yml` (extracted `items` only)
- RPM spec in `build/<name>.spec`

Local workflow:

```bash
make setup
make            # runs the generator, writes to build/
```

CI/CD workflow (prod-driven publish + specs branch + CircleCI):

- On the prod builder host, use Makefile targets to drive the flow.
- `make circleci-update` (on `main`): updates `.circleci` config when new distros appear and pushes to `origin/main`.
- `make update` (on `main`): runs the generator via venv, updates `build/`, `src/`, `trusted.yml`, and pushes to `origin/main`.
- `make specs-publish`: checks out `specs`, mirrors `build/`, `src/`, `.circleci` from `main`, regenerates top-level `*.xml` and `*.spec` via venv, commits only when changed, and pushes to `origin/specs`.
- CircleCI is configured to build from `specs`; the push from `specs-publish` triggers builds. If nothing changed, no rebuild occurs.

Versioning

- RPM `Version` is derived from upstream timestamps (JSON `creationTime` or HTTP `Last-Modified`) with fallback to today.
- The build workflow compares generated files via git diff; if nothing changed, CI won’t publish rebuilt artifacts.

Selectors

- `json_selector`: a dot path (or list of paths) to an array in JSON. Each array element can be:
  - a CIDR string (e.g., "1.2.3.0/24")
  - an object; use `json_value_keys` (string or list) to list field names that contain CIDRs. If not provided, all string values in the object (and strings within lists) are tried.
- `html_selector`: optional CSS selector to extract items from HTML; otherwise all lines of text are scanned.
```

Notes:
- `build/` is tracked in VCS to allow CI diffing; RPMs in `output/` are ignored.
- Specs are emitted into `build/` and consumed by rpmbuilder.
- The generator is compatible with Python 3.6+.

### Sources and selectors

- Each list in `trusted.yml` supports:
  - `url`: upstream endpoint
  - `json_selector`: dot-notated path (or list of paths) to extract array data from JSON
  - `json_value_keys`: string or list of keys whose values contain CIDRs (optional). If omitted, auto-detect from all string values.
  - `html_selector`: CSS selector to extract items from HTML (falls back to splitting lines of page text)

## TODO

* Optimize IP sets with https://github.com/firehol/iprange/wiki
* Install to `/usr/share/trusted-lists/plain/<name>.txt` and `/usr/share/trusted-lists/nginx/<name>.conf`

## Future

This project is to be complemented by another, e.g. [server-lists](https://github.com/dvershinin/server-lists).
The idea is that you reduce bot traffic by blocking all remote servers in `server-lists` project, while whitelisting the ones from `trusted-lists`.
