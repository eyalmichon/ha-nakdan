"""Services for Nakdan integration."""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_GET_NIKUD,
    SERVICE_CLEAR_CACHE,
    ATTR_TEXT,
    ATTR_ORIGINAL_TEXT,
    ATTR_NIKUD_TEXT,
    ATTR_RESPONSE_TIME,
    ATTR_CACHE_STATS,
    GENRES,
    MAX_TEXT_LENGTH,
)
from .nakdan_api import NakdanAPI

_LOGGER = logging.getLogger(__name__)

SERVICE_GET_NIKUD_SCHEMA = vol.Schema({
    vol.Required(ATTR_TEXT): cv.string,
    vol.Optional("genre", default="modern"): vol.In(GENRES),
})

SERVICE_CLEAR_CACHE_SCHEMA = vol.Schema({})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Nakdan integration."""

    def _update_sensor_if_available(text: str, result: str | None = None, success: bool = True, cache_stats: dict | None = None, count_requests: bool = True):
        """Update sensor stats if sensor is available."""
        try:
            sensor = hass.data.get(DOMAIN, {}).get("sensor")
            if sensor and hasattr(sensor, 'update_stats'):
                sensor.update_stats({
                    "text": text,
                    "result": result,
                    "success": success,
                    "cache_stats": cache_stats,
                }, count_requests)
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

        if not text or not text.strip():
            return {"success": False, "error": "Text cannot be empty"}
        if len(text) > MAX_TEXT_LENGTH:
            return {"success": False, "error": f"Text too long (maximum {MAX_TEXT_LENGTH} characters)"}

        try:
            # Call the service
            result = await api.get_nikud(text=text, genre=genre)

            if result is None:
                # Update sensor with failure
                _update_sensor_if_available(text, None, False, api.get_cache_stats())

                return {
                    "success": False,
                    "error": "Failed to get nikud from service"
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

            # Update sensor with cache operation
            _update_sensor_if_available(
                text="Cache cleared",
                result=f"Cleared {cleared_count} entries",
                success=True,
                cache_stats=api.get_cache_stats(),
                count_requests=False
            )

            _LOGGER.info("Cache cleared successfully: %d entries removed", cleared_count)
            return {
                "success": True,
                "cleared_entries": cleared_count,
                "cache_stats_before": cache_stats_before,
                "message": f"Successfully cleared {cleared_count} cache entries"
            }

        except Exception as err:
            # Update sensor with failure
            _update_sensor_if_available(
                text="Cache clear operation",
                result=None,
                success=False,
                cache_stats=api.get_cache_stats(),
                count_requests=False
            )

            _LOGGER.error("Error clearing cache: %s", err)
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

    _LOGGER.info("Nakdan services registered successfully")