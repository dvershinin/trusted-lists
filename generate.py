#!/usr/bin/env python3
from xml.etree.ElementTree import Element

import requests
import yaml
from bs4 import BeautifulSoup
from ipaddress import IPv4Network, AddressValueError, IPv6Network, get_mixed_type_key
from lxml import etree
from datetime import datetime
import os
import re
from jinja2 import Environment, FileSystemLoader
from email.utils import parsedate_to_datetime

def try_add_ip_or_range(network_s, networks):
    try:
        networks.append(
            IPv4Network(network_s)
        )
    except AddressValueError:
        try:
            networks.append(
                IPv6Network(network_s)
            )
        except AddressValueError:
            pass


script_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(script_dir, "build")
os.makedirs(build_dir, exist_ok=True)

env = Environment(loader=FileSystemLoader(os.path.join(script_dir, "src")))
ipset_spec_tpl = env.get_template("ipset.spec.j2")

with open(os.path.join(script_dir, "trusted.yml"), "r") as stream:
    try:
        trusted_lists = yaml.safe_load(stream)

        for list_name, list_config in trusted_lists.items():
            print(list_name)
            print(list_config)
            networks = []
            list_content_r = requests.get(
                list_config['url'],
                headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                    'cookie': 'enforce_policy=ccpa; LANG=en_US%3BUS; tsrce=smarthelpnodeweb',
                }
            )
            content_type = list_content_r.headers['content-type'].split(';').pop(0).strip()
            # Default version base: try upstream creationTime or Last-Modified; fallback to today's date (as string)
            base_version_value = datetime.utcnow().strftime('%Y%m%d')
            if content_type == 'text/plain':
                list_items = list_content_r.text.splitlines()
                print(list_items)
                for item in list_items:
                    try_add_ip_or_range(item, networks)
                print(networks)
            elif content_type == 'application/json':
                data = list_content_r.json()
                # If upstream provides creationTime, prefer it for version base
                if isinstance(data, dict) and 'creationTime' in data:
                    try:
                        # Extract YYYY-MM-DD and convert to YYYYMMDD for Py3.6 compat
                        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(data['creationTime']))
                        if m:
                            base_version_value = f"{m.group(1)}{m.group(2)}{m.group(3)}"
                    except Exception:
                        pass
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
                    if 'html_selector' in list_config:
                        soup = BeautifulSoup(target_element, 'html.parser')
                        list_items = soup.select(list_config['html_selector'])
                        for item in list_items:
                            item = item.text
                            try_add_ip_or_range(item, networks)
                        print(list_items)
                    else:
                        # target_element can be a list of strings or dicts
                        for item in target_element:
                            if isinstance(item, dict):
                                # If configured, use specific value keys from YAML
                                value_keys = []
                                if 'json_value_keys' in list_config:
                                    if isinstance(list_config['json_value_keys'], list):
                                        value_keys = list_config['json_value_keys']
                                    else:
                                        value_keys = [list_config['json_value_keys']]
                                if value_keys:
                                    for k in value_keys:
                                        if k in item:
                                            v = item[k]
                                            if isinstance(v, list):
                                                for vv in v:
                                                    if isinstance(vv, str):
                                                        try_add_ip_or_range(vv, networks)
                                            elif isinstance(v, str):
                                                try_add_ip_or_range(v, networks)
                                else:
                                    # Auto-detect: try all string values
                                    for v in item.values():
                                        if isinstance(v, list):
                                            for vv in v:
                                                if isinstance(vv, str):
                                                    try_add_ip_or_range(vv, networks)
                                        elif isinstance(v, str):
                                            try_add_ip_or_range(v, networks)
                            else:
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
            networks = sorted(networks, key=get_mixed_type_key)

            # Try Last-Modified header as a version base if no creationTime-derived date
            if base_version_value == datetime.utcnow().strftime('%Y%m%d'):
                try:
                    last_mod = list_content_r.headers.get('last-modified') or list_content_r.headers.get('Last-Modified')
                    if last_mod:
                        dt = parsedate_to_datetime(last_mod)
                        base_version_value = dt.strftime('%Y%m%d')
                except Exception:
                    pass

            # Version derived purely from upstream timestamps
            version_value = base_version_value
            with open(os.path.join(build_dir, f"{list_name}.txt"), 'w') as f:
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
                os.path.join(build_dir, f'{list_name}.xml'),
                xml_declaration=True,
                encoding="utf-8",
                pretty_print=True
            )

            list_data = list_config.copy()
            list_data['name'] = list_name
            list_data['items'] = []
            for n in networks:
                list_data['items'].append(str(n))
            with open(os.path.join(build_dir, f'{list_name}.yml'), 'w') as f:
                yaml.dump(list_data, f)

            # Render RPM spec for this list (support summary vs long description)
            summary_value = list_data.get('summary', list_data.get('description', f"{list_name.capitalize()} FirewallD IP set"))
            long_desc_value = list_data.get('description', summary_value)
            spec_content = ipset_spec_tpl.render(
                name=list_name,
                version=version_value,
                url=list_data.get('url', ''),
                summary=summary_value,
                long_description=long_desc_value,
            )
            spec_path = os.path.join(build_dir, f"{list_name}.spec")
            with open(spec_path, 'w') as f:
                f.write(spec_content)

        # no persistent state; versions are derived from upstream timestamps
    except yaml.YAMLError as exc:
        print(exc)
