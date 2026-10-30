"""Small asynchronous IPWhois client. No credentials or arbitrary URLs."""

from __future__ import annotations

import asyncio
import ipaddress
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp

from .const import URL


class ApiError(Exception):
    """Lookup failed without exposing response data in logs."""


class RateLimited(ApiError):
    """The provider asked us to wait."""

    def __init__(self, seconds: float):
        self.seconds = max(1, seconds)
        super().__init__("IP lookup rate limited")


def retry_delay(value: str | None) -> float:
    """Honor numeric or HTTP-date Retry-After; default to daily quota reset."""
    if value:
        try:
            seconds = float(value)
            return max(1, seconds) if math.isfinite(seconds) else 86400
        except ValueError:
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return max(1, (dt - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 86400


class IpWhoisClient:
    """Serialize requests and retain cooldown across entry reloads."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.retry_at = 0.0
        self.lock = asyncio.Lock()

    async def async_fetch(self) -> dict[str, Any]:
        async with self.lock:
            remaining = self.retry_at - time.monotonic()
            if remaining > 0:
                raise RateLimited(remaining)
            try:
                async with asyncio.timeout(15):
                    async with self.session.get(URL, allow_redirects=False) as response:
                        if response.status == 429:
                            delay = retry_delay(response.headers.get("Retry-After"))
                            self.retry_at = time.monotonic() + delay
                            raise RateLimited(delay)
                        if response.status != 200:
                            raise ApiError(f"IP lookup HTTP status {response.status}")
                        data = await response.json()
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                raise ApiError("Unable to retrieve a valid IP lookup response") from err
            if not isinstance(data, dict) or data.get("success") is not True:
                raise ApiError("IP lookup returned an unsuccessful response")
            try:
                if not isinstance(data.get("ip"), str):
                    raise ValueError("IP must be a string")
                ipaddress.ip_address(data["ip"])
            except (KeyError, ValueError, TypeError) as err:
                raise ApiError("IP lookup response has no valid public IP field") from err
            if not isinstance(data.get("connection"), dict):
                raise ApiError("IP lookup response has no connection information")
            return data
