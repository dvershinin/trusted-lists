import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import try_add_ip_or_range, extract_with_regex, extract_json_value_keys


class TestRegexExtraction:
    def test_regex_extracts_ipv4(self):
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
        text = "Server IPs: 192.168.1.1 and 10.0.0.0/8 are used"
        matches = re.findall(pattern, text)
        assert matches == ["192.168.1.1", "10.0.0.0/8"]

    def test_extract_with_regex_function(self):
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
        text = "IPs: 1.2.3.4 and 5.6.7.0/24"
        ipv4 = []
        ipv6 = []
        extract_with_regex(text, pattern, ipv4, ipv6)
        assert len(ipv4) == 2
        assert len(ipv6) == 0

    def test_regex_ignores_invalid_ips(self):
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)'
        text = "Invalid: 999.999.999.999 Valid: 1.2.3.4"
        ipv4 = []
        ipv6 = []
        extract_with_regex(text, pattern, ipv4, ipv6)
        # 999.999.999.999 will be matched by regex but rejected by IPv4Network
        assert len(ipv4) == 1


class TestJsonValueKeysExtraction:
    def test_json_value_keys_extraction(self, sample_bot_json):
        keys = ["ipv4Prefix", "ipv6Prefix"]
        ipv4 = []
        ipv6 = []
        extract_json_value_keys(sample_bot_json["prefixes"], keys, ipv4, ipv6)
        assert len(ipv4) == 1
        assert len(ipv6) == 1

    def test_json_value_keys_ipv4_present(self, sample_bot_json):
        keys = ["ipv4Prefix", "ipv6Prefix"]
        ipv4 = []
        ipv6 = []
        extract_json_value_keys(sample_bot_json["prefixes"], keys, ipv4, ipv6)
        network_strs = [str(n) for n in ipv4]
        assert "66.249.64.0/19" in network_strs

    def test_json_value_keys_ipv6_present(self, sample_bot_json):
        keys = ["ipv4Prefix", "ipv6Prefix"]
        ipv4 = []
        ipv6 = []
        extract_json_value_keys(sample_bot_json["prefixes"], keys, ipv4, ipv6)
        network_strs = [str(n) for n in ipv6]
        assert "2001:4860:4801::/48" in network_strs

    def test_json_value_keys_missing_key(self):
        items = [{"ipv4Prefix": "1.2.3.0/24"}]
        keys = ["ipv4Prefix", "ipv6Prefix"]
        ipv4 = []
        ipv6 = []
        extract_json_value_keys(items, keys, ipv4, ipv6)
        assert len(ipv4) == 1
        assert len(ipv6) == 0

    def test_json_value_keys_empty_value(self):
        items = [{"ipv4Prefix": "", "ipv6Prefix": None}]
        keys = ["ipv4Prefix", "ipv6Prefix"]
        ipv4 = []
        ipv6 = []
        extract_json_value_keys(items, keys, ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 0


class TestTryAddIpOrRange:
    def test_add_valid_ipv4(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("192.168.1.0/24", ipv4, ipv6)
        assert len(ipv4) == 1
        assert len(ipv6) == 0

    def test_add_valid_ipv6(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("2001:db8::/32", ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 1

    def test_skip_empty_string(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("", ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 0

    def test_skip_whitespace(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("   ", ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 0

    def test_skip_none(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range(None, ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 0

    def test_strip_whitespace(self):
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("  10.0.0.0/8  ", ipv4, ipv6)
        assert len(ipv4) == 1
        assert len(ipv6) == 0
