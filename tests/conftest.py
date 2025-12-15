import pytest
import yaml


@pytest.fixture
def trusted_config():
    with open("trusted.yml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_bot_json():
    return {
        "prefixes": [
            {"ipv4Prefix": "66.249.64.0/19"},
            {"ipv6Prefix": "2001:4860:4801::/48"},
        ]
    }

