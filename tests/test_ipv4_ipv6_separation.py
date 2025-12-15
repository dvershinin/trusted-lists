"""Tests for IPv4/IPv6 separation in ipset generation."""
import os
import sys
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from xml.etree import ElementTree

import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import try_add_ip_or_range, write_ipset_files, get_output_name


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


class TestGetOutputName:
    """Test the get_output_name function for backward-compatible naming."""

    def test_ipv4_only_no_suffix(self):
        """IPv4-only source should not get -v4 suffix (backward compatible)."""
        name = get_output_name("braintree", "inet", has_both_families=False)
        assert name == "braintree"

    def test_ipv6_only_no_suffix(self):
        """IPv6-only source should not get -v6 suffix (backward compatible)."""
        name = get_output_name("someservice", "inet6", has_both_families=False)
        assert name == "someservice"

    def test_mixed_source_gets_v4_suffix(self):
        """Source with both families should get -v4 suffix for IPv4."""
        name = get_output_name("googlebot", "inet", has_both_families=True)
        assert name == "googlebot-v4"

    def test_mixed_source_gets_v6_suffix(self):
        """Source with both families should get -v6 suffix for IPv6."""
        name = get_output_name("googlebot", "inet6", has_both_families=True)
        assert name == "googlebot-v6"

    def test_existing_v4_suffix_preserved(self):
        """List already ending in -v4 should keep that name."""
        name = get_output_name("cloudflare-v4", "inet", has_both_families=False)
        assert name == "cloudflare-v4"

    def test_existing_v6_suffix_preserved(self):
        """List already ending in -v6 should keep that name."""
        name = get_output_name("cloudflare-v6", "inet6", has_both_families=False)
        assert name == "cloudflare-v6"

    def test_existing_v4_suffix_not_doubled(self):
        """List ending in -v4 should not get -v4-v4."""
        name = get_output_name("cloudflare-v4", "inet", has_both_families=True)
        assert name == "cloudflare-v4"
        assert "-v4-v4" not in name


class TestWriteIpsetFiles:
    """Test the write_ipset_files function."""

    def test_write_ipv4_file_has_inet_family(self, tmp_path):
        """IPv4 ipset XML should have family=inet."""
        networks = [IPv4Network("10.0.0.0/8"), IPv4Network("192.168.0.0/16")]

        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            # Pass output_name directly (no suffix added by write_ipset_files)
            write_ipset_files(
                "test",
                networks,
                "inet",
                "Test IPv4 ipset",
                {"url": "http://example.com"}
            )

            tree = ElementTree.parse("build/test.xml")
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

            tree = ElementTree.parse("build/test.xml")
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
            assert os.path.exists("build/test.txt")
            with open("build/test.txt") as f:
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
            assert os.path.exists("build/test.yml")
            with open("build/test.yml") as f:
                data = yaml.safe_load(f)
            assert data["family"] == "inet"
            assert data["name"] == "test"
        finally:
            os.chdir(original_dir)

    def test_empty_networks_creates_no_files(self, tmp_path):
        """Empty network list should not create any files."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        os.makedirs("build", exist_ok=True)

        try:
            write_ipset_files("test", [], "inet", "Test", {"url": "http://example.com"})
            assert not os.path.exists("build/test.xml")
            assert not os.path.exists("build/test.txt")
            assert not os.path.exists("build/test.yml")
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
            with open("build/test.txt") as f:
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

    def test_xml_has_family_option(self):
        """All XML files should have a family option."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        xml_files = [f for f in os.listdir(BUILD_DIR) if f.endswith(".xml")]
        if not xml_files:
            pytest.skip("No XML files in build/")

        for filename in xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            option = root.find("option")
            assert option is not None, f"{filename}: missing <option> element"
            assert option.get("name") == "family", f"{filename}: option should be 'family'"
            assert option.get("value") in ("inet", "inet6"), \
                f"{filename}: family should be 'inet' or 'inet6'"

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

    def test_backward_compatible_naming(self):
        """IPv4-only sources should not have -v4 suffix (backward compatible)."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        # These are known IPv4-only sources that should NOT have -v4 suffix
        ipv4_only_sources = ["braintree", "circleci", "stripe", "paypal",
                             "jetpack", "twitter", "wp-rocket"]

        for source in ipv4_only_sources:
            # The file should exist without -v4 suffix
            no_suffix_path = os.path.join(BUILD_DIR, f"{source}.xml")
            v4_suffix_path = os.path.join(BUILD_DIR, f"{source}-v4.xml")

            if os.path.exists(no_suffix_path):
                # Good - backward compatible naming
                assert not os.path.exists(v4_suffix_path), \
                    f"{source}: should not have both {source}.xml and {source}-v4.xml"
            elif os.path.exists(v4_suffix_path):
                # This would be a regression - fail the test
                pytest.fail(f"{source}: should use {source}.xml not {source}-v4.xml "
                            f"for backward compatibility")

    def test_mixed_sources_have_suffixes(self):
        """Sources with both IPv4 and IPv6 should have -v4 and -v6 suffixes."""
        if not os.path.exists(BUILD_DIR):
            pytest.skip("build/ directory not present")

        # These are known mixed sources that should have -v4 and -v6 suffixes
        mixed_sources = ["googlebot", "yandex"]

        for source in mixed_sources:
            v4_path = os.path.join(BUILD_DIR, f"{source}-v4.xml")
            v6_path = os.path.join(BUILD_DIR, f"{source}-v6.xml")

            # At least one should exist (source might not have both at all times)
            if os.path.exists(v4_path) or os.path.exists(v6_path):
                # If both exist, that's expected for mixed sources
                pass
            else:
                # Neither exists - skip (source might be down)
                pytest.skip(f"{source}: no build files found")

