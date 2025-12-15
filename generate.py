#!/usr/bin/env python3
import re
from xml.etree.ElementTree import Element

import requests
import yaml
from bs4 import BeautifulSoup
from ipaddress import IPv4Network, AddressValueError, IPv6Network, get_mixed_type_key
from lxml import etree


def try_add_ip_or_range(network_s, networks):
    """Try to parse and add an IP or network range to the list."""
    if not network_s or not network_s.strip():
        return
    network_s = network_s.strip()
    try:
        networks.append(IPv4Network(network_s))
    except (AddressValueError, ValueError):
        try:
            networks.append(IPv6Network(network_s))
        except (AddressValueError, ValueError):
            pass


def extract_with_regex(text, pattern, networks):
    """Extract IPs using a regex pattern."""
    compiled = re.compile(pattern)
    matches = compiled.findall(text)
    for match in matches:
        try_add_ip_or_range(match, networks)


def extract_json_value_keys(items, keys, networks):
    """Extract IPs from nested JSON objects using specified keys."""
    for item in items:
        if isinstance(item, dict):
            for key in keys:
                if key in item and item[key]:
                    try_add_ip_or_range(item[key], networks)


with open("trusted.yml", "r") as stream:
    try:
        trusted_lists = yaml.safe_load(stream)
        for list_name, list_config in trusted_lists.items():
            print(f"Processing: {list_name}")
            print(f"Config: {list_config}")
            networks = []
            # Choose headers based on config
            if list_config.get('simple_headers'):
                # Minimal headers for sites that block complex accept headers
                headers = {
                    'user-agent': 'Mozilla/5.0 (compatible; trusted-lists/1.0)',
                }
            else:
                # Full browser-like headers for most sites
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;'
                              'q=0.9,image/avif,image/webp,image/apng,*/*;'
                              'q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                }
            # PayPal requires specific cookies to access content
            if 'paypal.com' in list_config['url']:
                headers['cookie'] = 'enforce_policy=ccpa; LANG=en_US%3BUS; tsrce=smarthelpnodeweb'

            list_content_r = requests.get(list_config['url'], headers=headers)
            content_type = list_content_r.headers['content-type'].split(';').pop(0).strip()

            # Regex extraction (can work with any content type)
            if 'regex' in list_config:
                # If html_selector is specified, extract from that element first
                if 'html_selector' in list_config:
                    soup = BeautifulSoup(list_content_r.text, 'html.parser')
                    html_elems = soup.select(list_config['html_selector'])
                    for elem in html_elems:
                        extract_with_regex(elem.get_text(), list_config['regex'], networks)
                else:
                    extract_with_regex(list_content_r.text, list_config['regex'], networks)
                print(f"Extracted {len(networks)} networks via regex")

            elif content_type == 'text/plain':
                list_items = list_content_r.text.splitlines()
                print(list_items)
                for item in list_items:
                    try_add_ip_or_range(item, networks)
                print(networks)

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
                    print(target_element)

                    # New: json_value_keys extraction for nested objects
                    if 'json_value_keys' in list_config:
                        extract_json_value_keys(
                            target_element,
                            list_config['json_value_keys'],
                            networks
                        )
                    elif 'html_selector' in list_config:
                        soup = BeautifulSoup(target_element, 'html.parser')
                        list_items = soup.select(list_config['html_selector'])
                        for item in list_items:
                            try_add_ip_or_range(item.text, networks)
                        print(list_items)
                    else:
                        for item in target_element:
                            try_add_ip_or_range(item, networks)
                print(networks)

            elif content_type == 'text/html':
                soup = BeautifulSoup(list_content_r.text, 'html.parser')
                print(list_content_r)
                list_items = []
                if 'html_selector' in list_config:
                    html_elems = soup.select(list_config['html_selector'])
                    for elem in html_elems:
                        list_items.append(elem.text)
                else:
                    list_items = soup.text.splitlines()
                for item in list_items:
                    try_add_ip_or_range(item, networks)
                print(networks)

            # Deduplicate and sort networks
            networks = sorted(set(networks), key=get_mixed_type_key)
            print(f"Total networks for {list_name}: {len(networks)}")

            with open(f"./build/{list_name}.txt", 'w') as f:
                for n in networks:
                    f.write(str(n) + "\n")

            root: Element = etree.Element('ipset')
            root.set('type', 'hash:net')
            description = list_name.capitalize() + " FirewallD IP Set"
            if 'description' in list_config:
                description = list_config['description']
            etree.SubElement(root, 'description').text = description
            for n in networks:
                etree.SubElement(root, 'entry').text = str(n)
            root.getroottree().write(
                f'./build/{list_name}.xml',
                xml_declaration=True,
                encoding="utf-8",
                pretty_print=True
            )

            list_data = list_config.copy()
            list_data['name'] = list_name
            list_data['items'] = []
            for n in networks:
                list_data['items'].append(str(n))
            with open(f'./build/{list_name}.yml', 'w') as f:
                yaml.dump(list_data, f)
    except yaml.YAMLError as exc:
        print(exc)
