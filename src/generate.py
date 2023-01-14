#!/usr/bin/env python3
from xml.etree.ElementTree import Element

import requests
import yaml
from bs4 import BeautifulSoup
from ipaddress import IPv4Network, AddressValueError, IPv6Network, get_mixed_type_key
from lxml import etree

def try_add_ip_or_range(network_s, networks):
    try:
        networks.append(
            IPv4Network(item)
        )
    except AddressValueError:
        try:
            networks.append(
                IPv6Network(item)
            )
        except AddressValueError:
            pass


with open("trusted.yml", "r") as stream:
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
            if content_type == 'text/plain':
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
                    if 'html_selector' in list_config:
                        soup = BeautifulSoup(target_element, 'html.parser')
                        list_items = soup.select(list_config['html_selector'])
                        for item in list_items:
                            item = item.text
                            try_add_ip_or_range(item, networks)
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
            networks = sorted(networks, key=get_mixed_type_key)
            with open(f"../build/{list_name}.txt", 'a') as f:
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
                f'../build/{list_name}.xml',
                xml_declaration=True,
                encoding="utf-8",
                pretty_print=True
            )
    except yaml.YAMLError as exc:
        print(exc)
