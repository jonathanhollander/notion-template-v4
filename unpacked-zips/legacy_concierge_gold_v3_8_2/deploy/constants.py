"""Constants for Notion API deployment script."""

# API Configuration
NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2024-05-22"  # Updated from 2022-06-28

# API Endpoints
ENDPOINT_SEARCH = f"{NOTION_API_BASE_URL}/search"
ENDPOINT_PAGES = f"{NOTION_API_BASE_URL}/pages"
ENDPOINT_DATABASES = f"{NOTION_API_BASE_URL}/databases"
ENDPOINT_BLOCKS = f"{NOTION_API_BASE_URL}/blocks"

# Page Titles
PAGES_INDEX_TITLE = "Admin – Pages Index"
LIBRARY_TITLE = "Library"
FILES_LIBRARY_TITLE = "Files Library"

# Database Properties
STATUS_DONE = "Done"
CHECK_FORMULA = 'if(prop("Status") == "Done", "✅", "")'

# Pagination
DEFAULT_PAGE_SIZE = 100
QUERY_PAGE_SIZE = 10
SMALL_PAGE_SIZE = 5

# Marker Strings
MARKER_PREFIX = "Marker:"
IDEMPOTENT_SUFFIX = " (idempotent)"

# File Processing
CSV_DELIMITER = ","
CSV_ENCODING = "utf-8"

# HTTP Configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Environment Variables
ENV_NOTION_TOKEN = "NOTION_TOKEN"
ENV_NOTION_VERSION = "NOTION_VERSION"
ENV_PARENT_PAGE_ID = "NOTION_PARENT_PAGEID"
ENV_ASSET_BASE_URL = "ASSET_BASE_URL"