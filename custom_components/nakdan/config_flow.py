"""Config flow for Nakdan integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_CACHE_DURATION, DEFAULT_MAX_CACHE_SIZE
from .nakdan_api import NakdanAPI

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("cache_duration", default=DEFAULT_CACHE_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=86400)
        ),
        vol.Optional("max_cache_size", default=DEFAULT_MAX_CACHE_SIZE): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=1000000)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect to the service."""
    api = NakdanAPI()

    try:
        # Test the service with a simple Hebrew word
        result = await api.get_nikud("שלום", "modern")
        if not result:
            raise CannotConnect
    except Exception as exc:
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect from exc

    return {"title": "Nakdan - Hebrew Nikud"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nakdan"""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the Nakdan service."""