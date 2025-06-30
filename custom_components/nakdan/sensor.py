"""Sensor platform for Nakdan integration."""
import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nakdan sensor."""
    sensor = NakdanSensor(config_entry)

    # Store sensor reference in hass.data for services to access
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["sensor"] = sensor

    async_add_entities([sensor], True)

class NakdanSensor(SensorEntity):
    """Nakdan sensor entity."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._attr_name = "Nakdan Status"
        self._attr_unique_id = f"{DOMAIN}_sensor"
        self._attr_icon = "mdi:format-text"

        # State attributes
        self._state = "Ready"
        self._last_text = None
        self._last_result = None
        self._last_update = None
        self._total_requests = 0
        self._failed_requests = 0
        self._cache_stats = {}

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        attributes = {
            "last_text": self._last_text,
            "last_result": self._last_result,
            "last_update": self._last_update,
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "success_rate": (
                round((self._total_requests - self._failed_requests) / self._total_requests * 100, 1)
                if self._total_requests > 0 else 0
            ),
            "cache_duration": self._config_entry.data.get("cache_duration", 3600),
            "max_cache_size": self._config_entry.data.get("max_cache_size", 1000),
        }

        # Add cache statistics if available
        if self._cache_stats:
            attributes.update({
                "cache_total_entries": self._cache_stats.get("total_entries", 0),
                "cache_valid_entries": self._cache_stats.get("valid_entries", 0),
                "cache_expired_entries": self._cache_stats.get("expired_entries", 0),
            })

        return attributes

    def update_stats(self, text: str, result: str | None = None, success: bool = True, cache_stats: dict | None = None) -> None:
        """Update sensor stats."""
        self._total_requests += 1
        if not success:
            self._failed_requests += 1
            self._state = "Error"
        else:
            self._state = "Ready"

        self._last_text = text[:100] if text else None  # Truncate for display
        self._last_result = result[:100] if result else None  # Truncate for display
        self._last_update = datetime.now().isoformat()

        # Update cache stats if provided
        if cache_stats:
            self._cache_stats = cache_stats

        # Schedule an update
        self.schedule_update_ha_state()