"""UI setup and polling options."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import ApiError, RateLimited
from .const import CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN, MAX_INTERVAL, MIN_INTERVAL, NAME
from .coordinator import get_client


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Allow one current-egress lookup per Home Assistant instance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            try:
                await get_client(self.hass).async_fetch()
            except RateLimited:
                errors["base"] = "rate_limited"
            except ApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlowWithReload):
    """Reload once after options change; no additional update listener."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL,
                        default=self.config_entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL, max=MAX_INTERVAL))
                }
            ),
        )
