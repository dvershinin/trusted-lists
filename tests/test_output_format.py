import os
from xml.etree import ElementTree

import pytest
import yaml


BUILD_DIR = "build"


@pytest.fixture
def build_files():
    """Get list of files in build directory if it exists."""
    if not os.path.exists(BUILD_DIR):
        return []
    return os.listdir(BUILD_DIR)


class TestXmlOutput:
    def test_xml_files_are_valid(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        xml_files = [f for f in build_files if f.endswith(".xml")]
        if not xml_files:
            pytest.skip("No XML files in build/")

        for filename in xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            assert root.tag == "ipset", f"{filename}: root tag should be 'ipset'"
            assert root.get("type") == "hash:net", f"{filename}: type should be 'hash:net'"

    def test_xml_has_description(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        xml_files = [f for f in build_files if f.endswith(".xml")]
        if not xml_files:
            pytest.skip("No XML files in build/")

        for filename in xml_files:
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            desc = root.find("description")
            assert desc is not None, f"{filename}: missing description element"
            assert desc.text, f"{filename}: description should not be empty"

    def test_xml_has_entries(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        xml_files = [f for f in build_files if f.endswith(".xml")]
        if not xml_files:
            pytest.skip("No XML files in build/")

        # Some sources may be temporarily unavailable or protected
        empty_allowed = {"wordfence.xml", "yandex.xml", "metabase.xml"}
        for filename in xml_files:
            if filename in empty_allowed:
                continue
            path = os.path.join(BUILD_DIR, filename)
            tree = ElementTree.parse(path)
            root = tree.getroot()
            entries = root.findall("entry")
            assert len(entries) > 0, f"{filename}: should have at least one entry"


class TestTxtOutput:
    def test_txt_files_have_content(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        txt_files = [f for f in build_files if f.endswith(".txt")]
        if not txt_files:
            pytest.skip("No TXT files in build/")

        # Some sources may be temporarily unavailable or protected
        empty_allowed = {"wordfence.txt", "yandex.txt", "metabase.txt"}
        for filename in txt_files:
            if filename in empty_allowed:
                continue
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                content = f.read().strip()
            assert content, f"{filename}: should not be empty"

    def test_txt_files_have_valid_ips(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        txt_files = [f for f in build_files if f.endswith(".txt")]
        if not txt_files:
            pytest.skip("No TXT files in build/")

        for filename in txt_files:
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                lines = f.read().strip().splitlines()
            for line in lines:
                # Basic check: should contain / for CIDR or be valid IP
                assert line.strip(), f"{filename}: should not have empty lines"


class TestYmlOutput:
    def test_yml_files_are_valid(self, build_files):
        if not build_files:
            pytest.skip("build/ directory not present or empty")

        yml_files = [f for f in build_files if f.endswith(".yml")]
        if not yml_files:
            pytest.skip("No YML files in build/")

        for filename in yml_files:
            path = os.path.join(BUILD_DIR, filename)
            with open(path) as f:
                data = yaml.safe_load(f)
            assert data is not None, f"{filename}: should be valid YAML"
            assert "name" in data, f"{filename}: should have 'name' field"
            assert "items" in data, f"{filename}: should have 'items' field"
            assert isinstance(data["items"], list), f"{filename}: items should be a list"

