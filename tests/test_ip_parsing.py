from ipaddress import IPv4Network, IPv6Network

import pytest


def test_valid_ipv4_cidr():
    net = IPv4Network("192.168.1.0/24")
    assert net.num_addresses == 256


def test_valid_ipv6_cidr():
    net = IPv6Network("2001:4860:4801::/48")
    assert net.prefixlen == 48


def test_single_ipv4():
    net = IPv4Network("1.2.3.4/32")
    assert str(net) == "1.2.3.4/32"


def test_single_ipv4_without_prefix():
    # When strict=False (default), single IP becomes /32
    net = IPv4Network("1.2.3.4")
    assert net.prefixlen == 32


def test_invalid_ip_raises():
    with pytest.raises(ValueError):
        IPv4Network("999.999.999.999")


def test_ipv6_single_address():
    net = IPv6Network("2001:4860:4801::1/128")
    assert net.prefixlen == 128


def test_large_ipv4_block():
    net = IPv4Network("10.0.0.0/8")
    assert net.num_addresses == 16777216


def test_cloudflare_style_range():
    """Test a typical Cloudflare-style IP range."""
    net = IPv4Network("103.21.244.0/22")
    assert net.num_addresses == 1024






