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


def write_ipset_files(output_name, networks, family, description, list_config):
    """Write TXT, XML, and YML files for an ipset.

    Args:
        output_name: The final output filename (without extension)
        networks: List of network objects (IPv4Network or IPv6Network)
        family: "inet" for IPv4, "inet6" for IPv6
        description: Description text for the ipset
        list_config: Original config dict from trusted.yml
    """
    if not networks:
        return

    # Deduplicate and sort
    networks = sorted(set(networks))

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
    etree.SubElement(root, 'description').text = description
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


def get_output_name(list_name, family, has_both_families):
    """Determine output filename based on naming strategy.

    Naming rules:
    1. If list_name already ends with -v4 or -v6, use as-is
    2. If source has BOTH IPv4 and IPv6, add -v4/-v6 suffix
    3. If source has only one family, use list_name without suffix (backward compatible)
    """
    if list_name.endswith("-v4") or list_name.endswith("-v6"):
        return list_name

    if has_both_families:
        suffix = "-v4" if family == "inet" else "-v6"
        return f"{list_name}{suffix}"

    # Single family - no suffix for backward compatibility
    return list_name


with open("trusted.yml", "r") as stream:
    try:
        trusted_lists = yaml.safe_load(stream)
        for list_name, list_config in trusted_lists.items():
            print(f"Processing: {list_name}")
            print(f"Config: {list_config}")
            ipv4_networks = []
            ipv6_networks = []

            # Handle static file sources (manually maintained)
            if 'static_file' in list_config:
                static_path = list_config['static_file']
                print(f"  Reading from static file: {static_path}")
                try:
                    with open(static_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            # Skip comments and empty lines
                            if not line or line.startswith('#'):
                                continue
                            try_add_ip_or_range(line, ipv4_networks, ipv6_networks)
                except FileNotFoundError:
                    print(f"  WARNING: Static file not found: {static_path}")
                    continue
            else:
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

            # Deduplicate before checking
            ipv4_networks = list(set(ipv4_networks))
            ipv6_networks = list(set(ipv6_networks))

            # Determine if source has both address families
            has_both_families = bool(ipv4_networks) and bool(ipv6_networks)

            # Check if list name already specifies a version
            has_version_suffix = list_name.endswith("-v4") or list_name.endswith("-v6")

            if has_version_suffix:
                # List already specifies version in config, write as-is
                if list_name.endswith("-v4"):
                    write_ipset_files(list_name, ipv4_networks, "inet",
                                      description, list_config)
                else:
                    write_ipset_files(list_name, ipv6_networks, "inet6",
                                      description, list_config)
            else:
                # Determine output names based on whether both families exist
                if ipv4_networks:
                    v4_name = get_output_name(list_name, "inet", has_both_families)
                    v4_desc = f"{description} (inet)" if has_both_families else description
                    write_ipset_files(v4_name, ipv4_networks, "inet",
                                      v4_desc, list_config)
                if ipv6_networks:
                    v6_name = get_output_name(list_name, "inet6", has_both_families)
                    v6_desc = f"{description} (inet6)" if has_both_families else description
                    write_ipset_files(v6_name, ipv6_networks, "inet6",
                                      v6_desc, list_config)

            total = len(ipv4_networks) + len(ipv6_networks)
            print(f"Total networks for {list_name}: {total}")

    except yaml.YAMLError as exc:
        print(exc)
