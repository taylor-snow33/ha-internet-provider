from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.rv_internet_provider.api import (
    ApiError,
    IpWhoisClient,
    RateLimited,
    retry_delay,
)


def client_for(data, status=200, headers=None):
    response = MagicMock(status=status, headers=headers or {})
    response.json = AsyncMock(return_value=data)
    session = MagicMock()
    session.get.return_value.__aenter__ = AsyncMock(return_value=response)
    session.get.return_value.__aexit__ = AsyncMock(return_value=False)
    return IpWhoisClient(session)


async def test_success(payload):
    c = client_for(payload)
    assert await c.async_fetch() == payload
    c.session.get.assert_called_once_with("https://ipwho.is/", allow_redirects=False)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"success": False, "message": "private"},
        {"success": True, "ip": "bad"},
        {"success": True, "ip": "8.8.4.4"},
    ],
)
async def test_invalid(payload):
    with pytest.raises(ApiError):
        await client_for(payload).async_fetch()


@pytest.mark.parametrize("status", [301, 403, 500])
async def test_http(status):
    with pytest.raises(ApiError):
        await client_for({}, status).async_fetch()


async def test_rate_limit():
    c = client_for({}, 429, {"Retry-After": "900"})
    with pytest.raises(RateLimited) as err:
        await c.async_fetch()
    assert err.value.seconds == 900
    with pytest.raises(RateLimited):
        await c.async_fetch()
    assert c.session.get.call_count == 1


@pytest.mark.parametrize(
    "error", [TimeoutError(), aiohttp.ClientError(), ValueError("invalid JSON")]
)
async def test_transport(error):
    c = client_for({})
    c.session.get.return_value.__aenter__.side_effect = error
    with pytest.raises(ApiError):
        await c.async_fetch()


def test_retry_delay():
    assert retry_delay(None) == 86400
    assert retry_delay("bad") == 86400
    assert retry_delay("-1") == 1
    assert retry_delay("Wed, 01 Jan 2020 00:00:00 GMT") == 1


@pytest.mark.parametrize("value", ["inf", "NaN", "-inf"])
def test_nonfinite_retry(value):
    assert retry_delay(value) == 86400


async def test_numeric_ip_rejected():
    with pytest.raises(ApiError):
        await client_for({"success": True, "ip": 123, "connection": {}}).async_fetch()
