"""One HTTPS request shared by every entity."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ApiError, IpWhoisClient, RateLimited
from .const import CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)


def get_client(hass: HomeAssistant) -> IpWhoisClient:
    """Reuse client for setup, options reloads, and retry cooldown."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = IpWhoisClient(async_get_clientsession(hass))
    return hass.data[DOMAIN]


class InternetCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate the current egress lookup, not whole-network health."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)),
        )
        self.client = get_client(hass)
        self.last_success = None

    async def _async_update_data(self):
        try:
            data = await self.client.async_fetch()
        except RateLimited as err:
            raise UpdateFailed("IP lookup quota reached", retry_after=err.seconds) from err
        except ApiError as err:
            raise UpdateFailed(str(err)) from err
        self.last_success = dt_util.utcnow()
        return data
