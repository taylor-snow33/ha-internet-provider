from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rv_internet_provider.api import ApiError, RateLimited
from custom_components.rv_internet_provider.const import DOMAIN


async def setup(hass, payload):
    entry = MockConfigEntry(domain=DOMAIN, title="RV Internet Provider", data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch", return_value=payload
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_setup_entities_unload(hass, payload):
    entry = await setup(hass, payload)
    states = hass.states.async_all()
    assert len(states) == 30
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "Example ISP"
    ip = hass.states.get("sensor.rv_internet_provider_public_ip")
    assert ip.state == "8.8.4.4"
    assert ip.attributes["response"] == payload
    assert hass.states.get("binary_sensor.rv_internet_provider_ip_country_in_eu").state == "off"
    assert (
        hass.states.get("binary_sensor.rv_internet_provider_ip_daylight_saving_time").state == "on"
    )
    assert entry.runtime_data.update_interval == timedelta(seconds=300)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "unavailable"


async def test_failure_and_recovery(hass, payload):
    entry = await setup(hass, payload)
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch",
        side_effect=ApiError("Lookup failed"),
    ):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "unavailable"
    assert "response" not in hass.states.get("sensor.rv_internet_provider_public_ip").attributes
    payload["connection"]["isp"] = "Backup ISP"
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch", return_value=payload
    ):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "Backup ISP"


async def test_missing_fields(hass, payload):
    payload.pop("timezone")
    await setup(hass, payload)
    assert hass.states.get("sensor.rv_internet_provider_ip_time_zone").state == "unavailable"
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "Example ISP"


async def test_flow_and_duplicate(hass, payload):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    with (
        patch(
            "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch",
            return_value=payload,
        ),
        patch("custom_components.rv_internet_provider.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "error,key", [(ApiError("fail"), "cannot_connect"), (RateLimited(60), "rate_limited")]
)
async def test_flow_errors(hass, error, key):
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch", side_effect=error
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={}
        )
    assert result["errors"] == {"base": key}


async def test_options_reload(hass, payload):
    entry = await setup(hass, payload)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch", return_value=payload
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"poll_interval": 600}
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["poll_interval"] == 600
    assert entry.runtime_data.update_interval == timedelta(seconds=600)


async def test_setup_failure(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch",
        side_effect=ApiError("fail"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)


async def test_rate_limit_unavailable_and_reload_cooldown(hass, payload):
    import time

    entry = await setup(hass, payload)
    client = entry.runtime_data.client
    client.retry_at = time.monotonic() + 600
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch",
        side_effect=RateLimited(600),
    ):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
    assert hass.states.get("sensor.rv_internet_provider_isp").state == "unavailable"
    with patch(
        "custom_components.rv_internet_provider.api.IpWhoisClient.async_fetch", return_value=payload
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.runtime_data.client is client
    assert client.retry_at > time.monotonic()


async def test_long_state_and_raw_preserved(hass, payload):
    payload["connection"]["isp"] = "x" * 300
    payload["additional_field"] = {"future": "value"}
    await setup(hass, payload)
    assert len(hass.states.get("sensor.rv_internet_provider_isp").state) == 255
    assert (
        hass.states.get("sensor.rv_internet_provider_public_ip").attributes["response"] == payload
    )


async def test_bad_timestamp(hass, payload):
    payload["timezone"]["current_time"] = "bad"
    await setup(hass, payload)
    assert hass.states.get("sensor.rv_internet_provider_provider_timestamp").state == "unknown"
