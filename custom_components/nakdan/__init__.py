"""Nakdan Integration for Home Assistant."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nakdan from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the singleton API client
    from .nakdan_api import NakdanAPI
    api_client = NakdanAPI()

    # Set the Home Assistant instance
    api_client.set_hass(hass)

    _LOGGER.info("Nakdan client initialized")

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services only once
    if not hass.services.has_service(DOMAIN, "get_nikud"):
        await async_setup_services(hass)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up sensor reference
        if DOMAIN in hass.data:
            hass.data[DOMAIN].pop("sensor", None)

        # Only remove services if this is the last config entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if len(entries) <= 1:  # This entry is being removed
            hass.services.async_remove(DOMAIN, "get_nikud")
            hass.services.async_remove(DOMAIN, "clear_cache")

    return unload_ok

async def async_setup_services(hass: HomeAssistant):
    """Set up services for the Nakdan integration."""
    from .services import async_setup_services as setup_services
    await setup_services(hass)