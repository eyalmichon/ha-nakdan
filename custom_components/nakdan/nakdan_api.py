"""API client for Nakdan service."""
import asyncio
import hashlib
import logging
import threading
import time
from typing import Dict, List, Optional, Any
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from .const import NAKDAN_API_URL, NAKDAN_API_HEADERS, NAKDAN_API_OPTIONS, GENRES, DEFAULT_TIMEOUT, DEFAULT_CACHE_DURATION, DEFAULT_MAX_CACHE_SIZE, DEFAULT_MAX_RETRIES

_LOGGER = logging.getLogger(__name__)

class NakdanError(HomeAssistantError):
    """Base exception for Nakdan errors."""

class NakdanInvalidGenreError(NakdanError):
    """Exception raised when an invalid genre is provided."""

class NakdanAPI:
    """API client for Nakdan service."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Create a new instance of NakdanAPI."""
        with cls._lock:
            if not cls._instance:
                cls._instance = super(NakdanAPI, cls).__new__(cls)
                cls._instance._hass = None
                cls._instance._session = None
                cls._instance._cache = {}
                cls._instance._cache_duration = DEFAULT_CACHE_DURATION
                cls._instance._max_cache_size = DEFAULT_MAX_CACHE_SIZE
                cls._instance._initialized = True
        return cls._instance

    def update_config(self, cache_duration: int = None, max_cache_size: int = None, hass: HomeAssistant = None) -> None:
        """Update configuration settings explicitly."""
        if cache_duration is not None:
            old_duration = self._cache_duration
            self._cache_duration = cache_duration
            _LOGGER.info("Updated cache duration from %d to %d seconds", old_duration, cache_duration)

            # If cache duration is shorter, clean up expired entries immediately
            if cache_duration < old_duration:
                self._cleanup_expired_cache()

        if max_cache_size is not None:
            old_size = self._max_cache_size
            self._max_cache_size = max_cache_size
            _LOGGER.info("Updated max cache size from %d to %d entries", old_size, max_cache_size)

            # If new size is smaller, trim cache immediately
            if max_cache_size < old_size and len(self._cache) > max_cache_size:
                self._trim_cache_to_size()

        if hass is not None:
            self._hass = hass
            _LOGGER.debug("Updated Home Assistant instance reference")

    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "cache_duration": self._cache_duration,
            "max_cache_size": self._max_cache_size,
            "cache_stats": self.get_cache_stats(),
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session."""
        if self._hass:
            return async_get_clientsession(self._hass)
        else:
            if not self._session:
                self._session = aiohttp.ClientSession()
            return self._session

    async def close(self):
        """Close the session if we created it."""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_cache_key(self, text: str, genre: str) -> str:
        """Generate cache key for the request."""
        # Use SHA256 to avoid hash collisions
        content = f"{genre}_{text}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - timestamp < self._cache_duration

    def _cleanup_expired_cache(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._cache_duration
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            _LOGGER.debug("Cleaned up %d expired cache entries", len(expired_keys))

    def clear_cache(self) -> int:
        """Clear all cache entries and return count of cleared entries."""
        count = len(self._cache)
        self._cache.clear()
        _LOGGER.info("Cleared %d cache entries", count)
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = sum(
            1 for _, timestamp in self._cache.values()
            if current_time - timestamp < self._cache_duration
        )
        expired_entries = len(self._cache) - valid_entries

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_duration": self._cache_duration,
        }

    def _trim_cache_to_size(self) -> None:
        """Trim cache to max size by removing oldest entries."""
        if len(self._cache) <= self._max_cache_size:
            return

        entries_to_remove = len(self._cache) - self._max_cache_size
        oldest_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k][1]
        )[:entries_to_remove]

        for key in oldest_keys:
            del self._cache[key]

        _LOGGER.debug("Trimmed cache: removed %d entries to fit max size %d",
                     entries_to_remove, self._max_cache_size)

    async def get_nikud(self, text: str, genre: str = "modern", max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict[str, Any]]:
        """Get nikud for Hebrew text with retry logic."""

        # Validate genre
        if genre not in GENRES:
            raise NakdanInvalidGenreError(f"Invalid genre: {genre}")

        # Check cache
        cache_key = self._get_cache_key(text, genre)
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                _LOGGER.debug("Using cached result for: %s", text[:50])
                return cached_data
            else:
                # Remove expired entry
                del self._cache[cache_key]

        # Enforce cache size limit to prevent memory leaks
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k][1]
            )[:100]  # Remove 100 oldest entries
            for key in oldest_keys:
                del self._cache[key]
            _LOGGER.debug("Cache size limit reached, removed %d old entries", len(oldest_keys))

        # Periodically clean up expired entries (every 10th request)
        if len(self._cache) > 0 and len(self._cache) % 10 == 0:
            self._cleanup_expired_cache()

        payload = {
            "task": "nakdan",
            "data": text,
            "genre": genre,
            **NAKDAN_API_OPTIONS
        }

        start_time = time.time()

        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_session()
                timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)

                async with session.post(NAKDAN_API_URL, json=payload, headers=NAKDAN_API_HEADERS, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.json()

                        result_obj = {
                            "data": self.build_nikud_text(result),
                            "response_time": time.time() - start_time,
                            "attempts": attempt + 1
                        }

                        # Cache the result
                        self._cache[cache_key] = (result_obj, time.time())

                        if attempt > 0:
                            _LOGGER.info("Successfully got nikud for: %s (succeeded on attempt %d)", text[:50], attempt + 1)
                        else:
                            _LOGGER.debug("Successfully got nikud for: %s", text[:50])
                        return result_obj
                    else:
                        error_msg = f"API request failed with status {response.status}"
                        _LOGGER.warning("%s (attempt %d/%d)", error_msg, attempt + 1, max_retries + 1)

            except asyncio.TimeoutError as err:
                error_msg = "Timeout while calling Nakdan API"
                _LOGGER.warning("%s (attempt %d/%d)", error_msg, attempt + 1, max_retries + 1)
            except Exception as err:
                error_msg = f"Error calling Nakdan API: {err}"
                _LOGGER.warning("%s (attempt %d/%d)", error_msg, attempt + 1, max_retries + 1)

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s, 4s...
                _LOGGER.debug("Waiting %s seconds before retry", wait_time)
                await asyncio.sleep(wait_time)

        # All retries failed
        _LOGGER.error("All attempts failed for nikud request: %s", text[:50])
        return None

    def build_nikud_text(self, api_response: List[Dict[str, Any]]) -> str:
        """Build nikud text from API response."""
        if not api_response:
            return ""

        result_parts = []

        for item in api_response:
            if item.get("sep"):
                # This is a separator (space, punctuation, etc.)
                result_parts.append(item.get("word", ""))
            else:
                # This is a word with nikud options
                options = item.get("options", [])
                if options:
                    result_parts.append(options[0])
                else:
                    result_parts.append(item.get("word", ""))

        return "".join(result_parts)