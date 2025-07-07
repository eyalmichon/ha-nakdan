<div align="center">
  <img src="https://raw.githubusercontent.com/eyalmichon/brands/37447dc5ef47d6050b3a19db0a123bf9f9f59b7d/custom_integrations/nakdan/logo%402x.png" alt="Nakdan Logo" width="350">
</div>

# Nakdan - Hebrew Nikud Integration for Home Assistant

A custom Home Assistant integration that adds Hebrew nikud (vowel pointing) to text. This integration provides a persistent, cached solution with intelligent caching and multiple text genre support. This is very for Text to Speech (TTS) applications.

## Features

- **Add nikud to Hebrew text** using a professional Hebrew processing service
- **Intelligent caching** with hash-based keys to minimize service calls and improve performance
- **Multiple text genres** support (modern, rabbinic, modernpoetry, medievalpoetry)
- **Configurable cache settings** (duration and maximum size)
- **Status monitoring** through sensor entities with detailed statistics
- **Service responses** with detailed information and cache statistics
- **Automatic cache cleanup** of expired entries

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/eyalmichon/ha-nakdan`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Nakdan" and install

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/nakdan` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to Configuration → Integrations
5. Click "Add Integration"
6. Search for "Nakdan" and configure

## Configuration

The integration can be configured through the Home Assistant UI when you add the integration and later through update_config service:

- **Cache Duration**: How long to cache results in seconds (default: 3600 = 1 hour, range: 60-86400)
- **Max Cache Size**: Maximum number of cached entries (default: 1000, range: 10-1000000)

## Services

### `nakdan.get_nikud`

Adds nikud (vowel pointing) to Hebrew text.

**Parameters:**

- `text` (required): Hebrew text to process
- `genre` (optional): Text genre - `modern` (default), `rabbinic`, `modernpoetry`, `medievalpoetry`

**Response:**

```yaml
success: true
original_text: "שלום עולם"
nikud_text: "שָׁלוֹם עוֹלָם"
response_time: 0.234
cache_stats:
  total_entries: 5
  valid_entries: 5
  expired_entries: 0
  cache_duration: 3600
  cache_timeout_enabled: true
```

### `nakdan.clear_cache`

Clears all cached nikud results.

**Response:**

```yaml
success: true
cleared_entries: 12
cache_stats_before:
  total_entries: 12
  valid_entries: 8
  expired_entries: 4
  cache_duration: 3600
  cache_timeout_enabled: true
message: "Successfully cleared 12 cache entries"
```

### `nakdan.update_config`

Updates configuration settings without restarting Home Assistant.

**Parameters:**

- `enable_cache_timeout` (optional): New cache timeout in seconds
- `cache_duration` (optional): New cache duration in seconds
- `max_cache_size` (optional): New maximum cache size

**Response:**

```yaml
success: true
config_before:
  enable_cache_timeout: false
  cache_duration: 60
  max_cache_size: 1000
  cache_stats:
    total_entries: 0
    valid_entries: 0
    expired_entries: 0
    cache_duration: disabled
    cache_timeout_enabled: false
config_after:
  enable_cache_timeout: false
  cache_duration: 60
  max_cache_size: 1000
  cache_stats:
    total_entries: 0
    valid_entries: 0
    expired_entries: 0
    cache_duration: disabled
    cache_timeout_enabled: false
message: Configuration updated successfully
```

## Entities

### `sensor.nakdan_status`

Monitors the integration status and provides statistics:

**State:** Current status (`Ready`, `Error`)

**Attributes:**

- `last_text`: Last processed text (truncated to 100 characters)
- `last_result`: Last nikud result (truncated to 100 characters)
- `last_update`: Last processing timestamp (ISO format)
- `total_requests`: Total requests made
- `failed_requests`: Number of failed requests
- `success_rate`: Success rate percentage
- `cache_duration`: Current cache duration setting
- `max_cache_size`: Current max cache size setting
- `enable_cache_timeout`: Current cache timeout setting
- `cache_total_entries`: Total entries in cache
- `cache_valid_entries`: Number of valid (non-expired) entries
- `cache_expired_entries`: Number of expired entries

## Usage Examples

### Basic Automation Example

#TODO: Add examples


## Troubleshooting

### Service Not Available

- Ensure the integration is properly installed and configured
- Check that Home Assistant has been restarted after installation
- Verify the integration appears in Settings → Integrations

### Connection Issues

- Check your internet connection
- Check Home Assistant logs for detailed error messages
- Try the `clear_cache` service to reset any corrupted cache entries

### Cache Issues

- Use `nakdan.clear_cache` to reset the cache (this is not really needed, just in case someone wants to do it)
- Check cache statistics through the sensor entity
- Adjust cache duration based on your usage patterns
- Monitor cache size if you process large amounts of text

## Technical Details

### Dependencies

- **aiohttp**: For async HTTP requests (≥3.8.0)
- **Home Assistant Core**: Uses built-in client session for optimal performance

## Development

To contribute to this integration:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with different Hebrew texts and genres
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker at:
https://github.com/eyalmichon/ha-nakdan/issues

## Acknowledgments

- Hebrew processing service providers for enabling nikud functionality
