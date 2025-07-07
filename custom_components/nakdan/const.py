"""Constants for the Nakdan integration."""

DOMAIN = "nakdan"

# Configuration
CONF_TIMEOUT = "timeout"
CONF_ENABLE_CACHE_TIMEOUT = "enable_cache_timeout"
CONF_CACHE_DURATION = "cache_duration"
CONF_MAX_CACHE_SIZE = "max_cache_size"

# Defaults
DEFAULT_TIMEOUT = 15
DEFAULT_CACHE_DURATION = 3600  # 1 hour in seconds
DEFAULT_MAX_CACHE_SIZE = 1000  # Maximum number of cached entries
DEFAULT_MAX_RETRIES = 1  # Number of retries on failure
DEFAULT_ENABLE_CACHE_TIMEOUT = False  # Enable cache timeout by default

# Limits
MAX_TEXT_LENGTH = 10000  # Maximum characters allowed in text input

# API Configuration
NAKDAN_API_URL = "https://nakdan-u1-0.loadbalancer.dicta.org.il/api"
NAKDAN_API_HEADERS = {
    "accept": "application/json",
    "content-type": "text/plain;charset=UTF-8"
}
NAKDAN_API_OPTIONS = {
    "addmorph": False,
    "keepmetagim": False,
    "keepqq": False,
    "nodageshdefmem": False,
    "patachma": False,
    "useTokenization": False,
}
GENRES = [
    "modern",
    "rabbinic",
    "modernpoetry",
    "medievalpoetry"
]

# Service names
SERVICE_GET_NIKUD = "get_nikud"
SERVICE_CLEAR_CACHE = "clear_cache"

# Attributes
ATTR_TEXT = "text"
ATTR_ORIGINAL_TEXT = "original_text"
ATTR_NIKUD_TEXT = "nikud_text"
ATTR_RESPONSE_TIME = "response_time"
ATTR_CACHE_STATS = "cache_stats"