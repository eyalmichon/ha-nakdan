"""Services for Nakdan integration."""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_GET_NIKUD,
    SERVICE_CLEAR_CACHE,
    SERVICE_UPDATE_CONFIG,
    ATTR_TEXT,
    ATTR_ORIGINAL_TEXT,
    ATTR_NIKUD_TEXT,
    ATTR_RESPONSE_TIME,
    ATTR_CACHE_STATS,
    CONF_CACHE_DURATION,
    CONF_MAX_CACHE_SIZE,
    GENRES,
)
from .nakdan_api import NakdanAPI

_LOGGER = logging.getLogger(__name__)

SERVICE_GET_NIKUD_SCHEMA = vol.Schema({
    vol.Required(ATTR_TEXT): cv.string,
    vol.Optional("genre", default="modern"): vol.In(GENRES),
})

SERVICE_CLEAR_CACHE_SCHEMA = vol.Schema({})

SERVICE_UPDATE_CONFIG_SCHEMA = vol.Schema({
    vol.Optional(CONF_CACHE_DURATION): cv.positive_int,
    vol.Optional(CONF_MAX_CACHE_SIZE): vol.All(cv.positive_int, vol.Range(min=10, max=100000)),
})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Nakdan integration."""

    def _update_sensor_if_available(text: str, result: str | None = None, success: bool = True, cache_stats: dict | None = None):
        """Update sensor stats if sensor is available."""
        try:
            sensor = hass.data.get(DOMAIN, {}).get("sensor")
            if sensor and hasattr(sensor, 'update_stats'):
                sensor.update_stats(text, result, success, cache_stats)
            else:
                _LOGGER.debug("Sensor not available for stats update")
        except Exception as err:
            _LOGGER.warning("Failed to update sensor stats: %s", err)

    async def handle_get_nikud(call: ServiceCall) -> ServiceResponse:
        """Handle the get_nikud service call."""
        text = call.data[ATTR_TEXT]
        genre = call.data.get("genre", "modern")

        # Get the singleton API client
        api = NakdanAPI()

        try:
            # Call the API
            result = await api.get_nikud(text=text, genre=genre)

            if result is None:
                # Update sensor with failure
                _update_sensor_if_available(text, None, False, api.get_cache_stats())

                return {
                    "success": False,
                    "error": "Failed to get nikud from API"
                }

            nikud_text = result.get("data", "")

            # Update sensor with success
            _update_sensor_if_available(text, nikud_text, True, api.get_cache_stats())

            response_data = {
                "success": True,
                ATTR_ORIGINAL_TEXT: text,
                ATTR_NIKUD_TEXT: nikud_text,
                ATTR_RESPONSE_TIME: result.get("response_time", 0),
                ATTR_CACHE_STATS: api.get_cache_stats(),
            }

            _LOGGER.debug("Successfully processed nikud for text: %s", text[:50])
            return response_data

        except Exception as err:
            # Update sensor with failure
            _update_sensor_if_available(text, None, False, api.get_cache_stats())

            _LOGGER.error("Error in get_nikud service: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def handle_clear_cache(call: ServiceCall) -> ServiceResponse:
        """Handle the clear_cache service call."""
        # Get the singleton API client
        api = NakdanAPI()

        try:
            # Get cache stats before clearing
            cache_stats_before = api.get_cache_stats()

            # Clear the cache
            cleared_count = api.clear_cache()

            _LOGGER.info("Cache cleared successfully: %d entries removed", cleared_count)
            return {
                "success": True,
                "cleared_entries": cleared_count,
                "cache_stats_before": cache_stats_before,
                "message": f"Successfully cleared {cleared_count} cache entries"
            }

        except Exception as err:
            _LOGGER.error("Error clearing cache: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def handle_update_config(call: ServiceCall) -> ServiceResponse:
        """Handle the update_config service call."""
        # Get the singleton API client
        api = NakdanAPI()

        try:
            # Get current config before update
            config_before = api.get_current_config()

            # Update configuration
            api.update_config(
                cache_duration=call.data.get(CONF_CACHE_DURATION),
                max_cache_size=call.data.get(CONF_MAX_CACHE_SIZE)
            )

            # Get new config after update
            config_after = api.get_current_config()

            _LOGGER.info("Configuration updated successfully")
            return {
                "success": True,
                "config_before": config_before,
                "config_after": config_after,
                "message": "Configuration updated successfully"
            }

        except Exception as err:
            _LOGGER.error("Error updating configuration: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    # Register the services
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_NIKUD,
        handle_get_nikud,
        schema=SERVICE_GET_NIKUD_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_CACHE,
        handle_clear_cache,
        schema=SERVICE_CLEAR_CACHE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_CONFIG,
        handle_update_config,
        schema=SERVICE_UPDATE_CONFIG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    _LOGGER.info("Nakdan services registered successfully")