import json
from pathlib import Path

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def payload():
    return json.loads((Path(__file__).parent / "fixtures/success.json").read_text())
