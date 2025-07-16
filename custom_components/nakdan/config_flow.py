"""Config flow for Nakdan integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_ENABLE_CACHE_TIMEOUT, DEFAULT_CACHE_DURATION, DEFAULT_MAX_CACHE_SIZE
from .nakdan_api import NakdanAPI

_LOGGER = logging.getLogger(__name__)

# STEP_USER_DATA_SCHEMA = vol.Schema(
#     {
#         vol.Optional("enable_cache_timeout", default=DEFAULT_ENABLE_CACHE_TIMEOUT): bool,
#         vol.Optional("cache_duration", default=DEFAULT_CACHE_DURATION): vol.All(
#             vol.Coerce(int), vol.Range(min=60, max=86400)
#         ),
#         vol.Optional("max_cache_size", default=DEFAULT_MAX_CACHE_SIZE): vol.All(
#             vol.Coerce(int), vol.Range(min=10, max=1000000)
#         ),
#     }
# )

def get_options_schema(config_entry: config_entries.ConfigEntry | None = None) -> vol.Schema:
    """Get the options schema for the config entry."""
    return vol.Schema(
        {
            vol.Optional("enable_cache_timeout", default=config_entry.data.get("enable_cache_timeout", DEFAULT_ENABLE_CACHE_TIMEOUT) if config_entry else DEFAULT_ENABLE_CACHE_TIMEOUT): bool,
            vol.Optional("cache_duration", default=config_entry.data.get("cache_duration", DEFAULT_CACHE_DURATION) if config_entry else DEFAULT_CACHE_DURATION): vol.All(
                vol.Coerce(int), vol.Range(min=60, max=86400)
            ),
            vol.Optional("max_cache_size", default=config_entry.data.get("max_cache_size", DEFAULT_MAX_CACHE_SIZE) if config_entry else DEFAULT_MAX_CACHE_SIZE): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=1000000)
            ),
        }
    )


async def validate_api(hass: HomeAssistant) -> dict[str, Any]:
    """Validate the user input allows us to connect to the service."""

    try:
        # Test the service with a simple Hebrew word
        result = await NakdanAPI.test_api(hass)
        if not result:
            raise CannotConnect
    except Exception as exc:
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect from exc

    return {"title": "Nakdan - Hebrew Nikud"}

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the Nakdan service."""

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nakdan"""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return OptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # If the user has already configured the integration, abort with already_configured
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            try:
                info = await validate_api(self.hass)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=get_options_schema(), errors=errors)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Nakdan integration."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry data (API will read from it automatically)
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload the config entry to apply the new settings
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        # Show form with current values
        options_schema = get_options_schema(self.config_entry)

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )