#!/usr/bin/env python3
import re
from xml.etree.ElementTree import Element

import requests
import yaml
from bs4 import BeautifulSoup
from ipaddress import IPv4Network, AddressValueError, IPv6Network
from lxml import etree


def try_add_ip_or_range(network_s, ipv4_networks, ipv6_networks):
    """Try to parse and add an IP or network range to the appropriate list."""
    if not network_s or not network_s.strip():
        return
    network_s = network_s.strip()
    try:
        ipv4_networks.append(IPv4Network(network_s))
    except (AddressValueError, ValueError):
        try:
            ipv6_networks.append(IPv6Network(network_s))
        except (AddressValueError, ValueError):
            pass


def extract_with_regex(text, pattern, ipv4_networks, ipv6_networks):
    """Extract IPs using a regex pattern."""
    compiled = re.compile(pattern)
    matches = compiled.findall(text)
    for match in matches:
        try_add_ip_or_range(match, ipv4_networks, ipv6_networks)


def extract_json_value_keys(items, keys, ipv4_networks, ipv6_networks):
    """Extract IPs from nested JSON objects using specified keys."""
    for item in items:
        if isinstance(item, dict):
            for key in keys:
                if key in item and item[key]:
                    try_add_ip_or_range(item[key], ipv4_networks, ipv6_networks)


def write_ipset_files(list_name, networks, family, description, list_config):
    """Write TXT, XML, and YML files for an ipset."""
    if not networks:
        return

    # Deduplicate and sort
    networks = sorted(set(networks))

    suffix = "-v4" if family == "inet" else "-v6"
    # Only add suffix if the original list doesn't already have -v4/-v6 in name
    if list_name.endswith("-v4") or list_name.endswith("-v6"):
        output_name = list_name
    else:
        output_name = f"{list_name}{suffix}"

    print(f"  Writing {output_name}: {len(networks)} networks ({family})")

    # Write TXT file
    with open(f"./build/{output_name}.txt", 'w') as f:
        for n in networks:
            f.write(str(n) + "\n")

    # Write XML file with proper family option
    root: Element = etree.Element('ipset')
    root.set('type', 'hash:net')
    etree.SubElement(root, 'option').set('name', 'family')
    root.find('option').set('value', family)
    desc_text = f"{description} ({family})"
    etree.SubElement(root, 'description').text = desc_text
    for n in networks:
        etree.SubElement(root, 'entry').text = str(n)
    root.getroottree().write(
        f'./build/{output_name}.xml',
        xml_declaration=True,
        encoding="utf-8",
        pretty_print=True
    )

    # Write YML file
    list_data = list_config.copy()
    list_data['name'] = output_name
    list_data['family'] = family
    list_data['items'] = [str(n) for n in networks]
    with open(f'./build/{output_name}.yml', 'w') as f:
        yaml.dump(list_data, f)


with open("trusted.yml", "r") as stream:
    try:
        trusted_lists = yaml.safe_load(stream)
        for list_name, list_config in trusted_lists.items():
            print(f"Processing: {list_name}")
            print(f"Config: {list_config}")
            ipv4_networks = []
            ipv6_networks = []

            # Choose headers based on config
            if list_config.get('simple_headers'):
                headers = {
                    'user-agent': 'Mozilla/5.0 (compatible; trusted-lists/1.0)',
                }
            else:
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;'
                              'q=0.9,image/avif,image/webp,image/apng,*/*;'
                              'q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                }
            if 'paypal.com' in list_config['url']:
                headers['cookie'] = 'enforce_policy=ccpa; LANG=en_US%3BUS; tsrce=smarthelpnodeweb'

            list_content_r = requests.get(list_config['url'], headers=headers)
            content_type = list_content_r.headers['content-type'].split(';').pop(0).strip()

            # Regex extraction
            if 'regex' in list_config:
                if 'html_selector' in list_config:
                    soup = BeautifulSoup(list_content_r.text, 'html.parser')
                    html_elems = soup.select(list_config['html_selector'])
                    for elem in html_elems:
                        extract_with_regex(elem.get_text(), list_config['regex'],
                                           ipv4_networks, ipv6_networks)
                else:
                    extract_with_regex(list_content_r.text, list_config['regex'],
                                       ipv4_networks, ipv6_networks)
                print(f"Extracted {len(ipv4_networks)} IPv4 + {len(ipv6_networks)} IPv6 via regex")

            elif content_type == 'text/plain':
                list_items = list_content_r.text.splitlines()
                for item in list_items:
                    try_add_ip_or_range(item, ipv4_networks, ipv6_networks)

            elif content_type == 'application/json':
                data = list_content_r.json()
                json_selectors = []
                if 'json_selector' in list_config:
                    if not isinstance(list_config['json_selector'], list):
                        json_selectors.append(list_config['json_selector'])
                    else:
                        json_selectors = list_config['json_selector']

                for json_selector in json_selectors:
                    json_parent_tree = json_selector.split('.')
                    target_element = data.copy()
                    for elem in json_parent_tree:
                        target_element = target_element[elem]

                    if 'json_value_keys' in list_config:
                        extract_json_value_keys(
                            target_element,
                            list_config['json_value_keys'],
                            ipv4_networks, ipv6_networks
                        )
                    elif 'html_selector' in list_config:
                        soup = BeautifulSoup(target_element, 'html.parser')
                        list_items = soup.select(list_config['html_selector'])
                        for item in list_items:
                            try_add_ip_or_range(item.text, ipv4_networks, ipv6_networks)
                    else:
                        for item in target_element:
                            try_add_ip_or_range(item, ipv4_networks, ipv6_networks)

            elif content_type == 'text/html':
                soup = BeautifulSoup(list_content_r.text, 'html.parser')
                list_items = []
                if 'html_selector' in list_config:
                    html_elems = soup.select(list_config['html_selector'])
                    for elem in html_elems:
                        list_items.append(elem.text)
                else:
                    list_items = soup.text.splitlines()
                for item in list_items:
                    try_add_ip_or_range(item, ipv4_networks, ipv6_networks)

            # Get description
            description = list_config.get('description',
                                          f"{list_name.capitalize()} FirewallD IP Set")

            # Determine if list name already specifies a version
            has_version_suffix = list_name.endswith("-v4") or list_name.endswith("-v6")

            if has_version_suffix:
                # List already specifies version, write as-is
                if list_name.endswith("-v4"):
                    write_ipset_files(list_name, ipv4_networks, "inet",
                                      description, list_config)
                else:
                    write_ipset_files(list_name, ipv6_networks, "inet6",
                                      description, list_config)
            else:
                # Auto-split into v4 and v6 variants
                write_ipset_files(list_name, ipv4_networks, "inet",
                                  description, list_config)
                write_ipset_files(list_name, ipv6_networks, "inet6",
                                  description, list_config)

            total = len(set(ipv4_networks)) + len(set(ipv6_networks))
            print(f"Total networks for {list_name}: {total}")

    except yaml.YAMLError as exc:
        print(exc)
