"""Tests for IPv4/IPv6 separation in ipset generation."""
import os
import sys
import tempfile
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import try_add_ip_or_range, write_ipset_files


BUILD_DIR = "build"


class TestTryAddIpOrRangeSeparation:
    """Test that try_add_ip_or_range correctly separates IPv4 and IPv6."""

    def test_ipv4_goes_to_ipv4_list(self):
        """IPv4 addresses should be added to the ipv4 list only."""
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("192.168.1.0/24", ipv4, ipv6)
        assert len(ipv4) == 1
        assert len(ipv6) == 0
        assert isinstance(ipv4[0], IPv4Network)

    def test_ipv6_goes_to_ipv6_list(self):
        """IPv6 addresses should be added to the ipv6 list only."""
        ipv4 = []
        ipv6 = []
        try_add_ip_or_range("2001:db8::/32", ipv4, ipv6)
        assert len(ipv4) == 0
        assert len(ipv6) == 1
        assert isinstance(ipv6[0], IPv6Network)

    def test_mixed_input_separates_correctly(self):
        """Mixed IPv4 and IPv6 inputs should be separated."""
        ipv4 = []
        ipv6 = []
        addresses = [
            "10.0.0.0/8",
            "2001:db8::/32",
            "172.16.0.0/12",
            "fe80::/10",
            "192.168.0.0/16",
            "::1/128",
        ]
        for addr in addresses:
            try_add_ip_or_range(addr, ipv4, ipv6)

        assert len(ipv4) == 3  # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        assert len(ipv6) == 3  # 2001:db8::/32, fe80::/10, ::1/128
        assert all(isinstance(n, IPv4Network) for n in ipv4)
        assert all(isinstance(n, IPv6Network) for n in ipv6)


class TestWriteIpsetFiles:
    """Test the write_ipset_files function."""

    def test_write_ipv4_file_has_inet_family(self, tmp_path):
        """IPv4 ipset XML should have family=inet."""
        # Create test networks
        networks = [IPv4Network("10.0.0.0/8"), IPv4Network("192.168.0.0/16")]

        # Temporarily change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files(
                "test",
                networks,
                "inet",
                "Test IPv4 ipset",
                {"url": "http://example.com"}
            )

            # Check XML has correct family
            tree = ElementTree.parse("build/test-v4.xml")
            root = tree.getroot()
            option = root.find("option")
            assert option is not None
            assert option.get("name") == "family"
            assert option.get("value") == "inet"
        finally:
            os.chdir(original_dir)

    def test_write_ipv6_file_has_inet6_family(self, tmp_path):
        """IPv6 ipset XML should have family=inet6."""
        networks = [IPv6Network("2001:db8::/32"), IPv6Network("fe80::/10")]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files(
                "test",
                networks,
                "inet6",
                "Test IPv6 ipset",
                {"url": "http://example.com"}
            )

            tree = ElementTree.parse("build/test-v6.xml")
            root = tree.getroot()
            option = root.find("option")
            assert option is not None
            assert option.get("name") == "family"
            assert option.get("value") == "inet6"
        finally:
            os.chdir(original_dir)

    def test_write_creates_txt_file(self, tmp_path):
        """write_ipset_files should create a .txt file."""
        networks = [IPv4Network("10.0.0.0/8")]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files("test", networks, "inet", "Test", {"url": "http://example.com"})
            assert os.path.exists("build/test-v4.txt")
            with open("build/test-v4.txt") as f:
                content = f.read().strip()
            assert "10.0.0.0/8" in content
        finally:
            os.chdir(original_dir)

    def test_write_creates_yml_file_with_family(self, tmp_path):
        """write_ipset_files should create a .yml file with family field."""
        networks = [IPv4Network("10.0.0.0/8")]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files("test", networks, "inet", "Test", {"url": "http://example.com"})
            assert os.path.exists("build/test-v4.yml")
            with open("build/test-v4.yml") as f:
                data = yaml.safe_load(f)
            assert data["family"] == "inet"
            assert data["name"] == "test-v4"
        finally:
            os.chdir(original_dir)

    def test_empty_networks_creates_no_files(self, tmp_path):
        """Empty network list should not create any files."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files("test", [], "inet", "Test", {"url": "http://example.com"})
            assert not os.path.exists("build/test-v4.xml")
            assert not os.path.exists("build/test-v4.txt")
            assert not os.path.exists("build/test-v4.yml")
        finally:
            os.chdir(original_dir)

    def test_existing_v4_suffix_not_duplicated(self, tmp_path):
        """List names ending in -v4 should not get another -v4 suffix."""
        networks = [IPv4Network("10.0.0.0/8")]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files(
                "cloudflare-v4",
                networks,
                "inet",
                "Cloudflare IPv4",
                {"url": "http://example.com"}
            )
            # Should create cloudflare-v4.xml, NOT cloudflare-v4-v4.xml
            assert os.path.exists("build/cloudflare-v4.xml")
            assert not os.path.exists("build/cloudflare-v4-v4.xml")
        finally:
            os.chdir(original_dir)

    def test_deduplication(self, tmp_path):
        """Duplicate networks should be deduplicated."""
        networks = [
            IPv4Network("10.0.0.0/8"),
            IPv4Network("10.0.0.0/8"),  # duplicate
            IPv4Network("192.168.0.0/16"),
        ]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files("test", networks, "inet", "Test", {"url": "http://example.com"})
            with open("build/test-v4.txt") as f:
                lines = f.read().strip().splitlines()
            assert len(lines) == 2  # Duplicates removed
        finally:
            os.chdir(original_dir)


class TestBuildOutputSeparation:
    """Test that actual build output has proper separation."""

    def test_v4_files_contain_only_ipv4(self):
        """Files with -v4 suffix should only contain IPv4 addresses."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        v4_txt_files = [f for f in os.listdir(BUILD_DIR) if f.endswith("-v4.txt")]
        if not v4_txt_files:
            pytest.skip("No -v4.txt files in build/")

        for filename in v4_txt_files:
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                lines = f.read().strip().splitlines()
            for line in lines:
                if not line.strip():
                    continue
                # IPv4 addresses contain dots, IPv6 addresses contain colons
                assert ":" not in line, f"{filename}: contains IPv6 address {line}"
                assert "." in line, f"{filename}: should contain IPv4 address"

    def test_v6_files_contain_only_ipv6(self):
        """Files with -v6 suffix should only contain IPv6 addresses."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        v6_txt_files = [f for f in os.listdir(BUILD_DIR) if f.endswith("-v6.txt")]
        if not v6_txt_files:
            pytest.skip("No -v6.txt files in build/")

        for filename in v6_txt_files:
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                lines = f.read().strip().splitlines()
            for line in lines:
                if not line.strip():
                    continue
                # IPv6 addresses contain colons
                assert ":" in line, f"{filename}: should contain IPv6 address"

    def test_v4_xml_has_inet_family(self):
        """XML files with -v4 suffix should have family=inet."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        v4_xml_files = [f for f in os.listdir(BUILD_DIR) if f.endswith("-v4.xml")]
        if not v4_xml_files:
            pytest.skip("No -v4.xml files in build/")

        for filename in v4_xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            option = root.find("option")
            assert option is not None, f"{filename}: missing <option> element"
            assert option.get("name") == "family", f"{filename}: option should be 'family'"
            assert option.get("value") == "inet", f"{filename}: family should be 'inet'"

    def test_v6_xml_has_inet6_family(self):
        """XML files with -v6 suffix should have family=inet6."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        v6_xml_files = [f for f in os.listdir(BUILD_DIR) if f.endswith("-v6.xml")]
        if not v6_xml_files:
            pytest.skip("No -v6.xml files in build/")

        for filename in v6_xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            option = root.find("option")
            assert option is not None, f"{filename}: missing <option> element"
            assert option.get("name") == "family", f"{filename}: option should be 'family'"
            assert option.get("value") == "inet6", f"{filename}: family should be 'inet6'"

    def test_yml_files_have_family_field(self):
        """YML files should have a 'family' field."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        yml_files = [f for f in os.listdir(BUILD_DIR) if f.endswith(".yml")]
        if not yml_files:
            pytest.skip("No YML files in build/")

        for filename in yml_files:
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                data = yaml.safe_load(f)
            assert "family" in data, f"{filename}: should have 'family' field"
            assert data["family"] in ("inet", "inet6"), \
                f"{filename}: family should be 'inet' or 'inet6'"

    def test_no_mixed_ipsets(self):
        """No ipset XML should contain both IPv4 and IPv6 addresses."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        xml_files = [f for f in os.listdir(BUILD_DIR) if f.endswith(".xml")]
        if not xml_files:
            pytest.skip("No XML files in build/")

        for filename in xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            entries = root.findall("entry")

            has_ipv4 = False
            has_ipv6 = False
            for entry in entries:
                text = entry.text or ""
                if ":" in text:
                    has_ipv6 = True
                elif "." in text:
                    has_ipv4 = True

            assert not (has_ipv4 and has_ipv6), \
                f"{filename}: should not contain both IPv4 and IPv6 addresses"

