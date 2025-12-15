import pytest


def test_config_is_not_empty(trusted_config):
    assert trusted_config is not None
    assert len(trusted_config) > 0


def test_all_entries_have_url(trusted_config):
    for name, config in trusted_config.items():
        assert "url" in config, f"{name} missing 'url' field"


def test_urls_are_http(trusted_config):
    for name, config in trusted_config.items():
        url = config["url"]
        assert url.startswith("http"), f"{name} has invalid URL: {url}"


def test_json_value_keys_requires_json_selector(trusted_config):
    for name, config in trusted_config.items():
        if "json_value_keys" in config:
            assert "json_selector" in config, \
                f"{name} has json_value_keys but no json_selector"


def test_json_value_keys_is_list(trusted_config):
    for name, config in trusted_config.items():
        if "json_value_keys" in config:
            assert isinstance(config["json_value_keys"], list), \
                f"{name} json_value_keys must be a list"


def test_regex_is_string(trusted_config):
    for name, config in trusted_config.items():
        if "regex" in config:
            assert isinstance(config["regex"], str), \
                f"{name} regex must be a string"


def test_description_is_optional_string(trusted_config):
    for name, config in trusted_config.items():
        if "description" in config:
            assert isinstance(config["description"], str), \
                f"{name} description must be a string"

