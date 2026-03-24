"""Project-wide constants for Economic Times scraping.

This module centralizes URLs, default HTTP settings, scraper limits, and
common markers such as paywall identifiers.
"""

from __future__ import annotations

BASE_URL = "https://economictimes.indiatimes.com"
HOMEPAGE_PATH = "/"

# Delay range (in seconds) between requests to reduce request bursts.
MIN_DELAY_SECONDS = 1.5
MAX_DELAY_SECONDS = 4.0

# How many items are retained from selected high-volume sections.
TOP_STORIES_LIMIT = 20
RELATED_ARTICLES_LIMIT = 10

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    # Keep encodings to formats decoded by default in our runtime.
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

PAYWALL_MARKERS = [
    "etprime",
    "prime.economictimes",
    "Subscribe to ET Prime",
    "ET Prime Story",
]
