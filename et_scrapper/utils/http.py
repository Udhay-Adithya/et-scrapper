"""HTTP client utilities for ET scraper with anti-detection headers."""

import asyncio
import random
from typing import Optional, Sequence

import httpx

from ..constants import BASE_URL, DEFAULT_HEADERS, MAX_DELAY_SECONDS, MIN_DELAY_SECONDS
from ..models import ArticleDetail, HomepageData


class ETHttpClient:
    """Asynchronous HTTP client and high-level API for ET scraping.

    Typical usage:

    ```python
    async with ETHttpClient() as client:
        homepage = await client.scrape_homepage()
        articles = await client.scrape_articles(["https://..."])
    ```

    Args:
        headers: Optional custom HTTP headers.
        timeout: Request timeout in seconds.
        follow_redirects: Whether redirects should be followed.
    """

    def __init__(
        self,
        headers: Optional[dict] = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ):
        """Initialize HTTP client configuration.

        Args:
            headers: Optional custom HTTP headers.
            timeout: Request timeout in seconds.
            follow_redirects: Whether redirects should be followed.
        """
        self.headers = headers or DEFAULT_HEADERS
        self.timeout = httpx.Timeout(timeout)
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ETHttpClient":
        """Open the underlying ``httpx.AsyncClient`` and return self."""
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Close the underlying HTTP client when leaving context."""
        if self._client:
            await self._client.aclose()

    async def _random_delay(self) -> None:
        """Sleep for a random interval to avoid rate limiting."""
        delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        await asyncio.sleep(delay)

    async def get(self, url: str, delay: bool = True) -> httpx.Response:
        """Perform a GET request, optionally with a random delay before."""
        if self._client is None:
            raise RuntimeError("Client not initialised. Use async context manager.")
        if delay:
            await self._random_delay()
        response = await self._client.get(url)
        response.raise_for_status()
        return response

    async def get_page(self, path: str = "", delay: bool = True) -> httpx.Response:
        """Fetch a page relative to the ET base URL."""
        url = BASE_URL + path if not path.startswith("http") else path
        return await self.get(url, delay=delay)

    async def scrape_homepage(self) -> HomepageData:
        """Scrape the ET homepage and return structured homepage data."""
        from ..scrapers.homepage import HomepageScraper

        scraper = HomepageScraper(self)
        return await scraper.scrape()

    async def scrape_article(self, url: str) -> ArticleDetail | None:
        """Scrape one ET article URL.

        Returns ``None`` when the article is paywalled.
        """
        from ..scrapers.article import ArticleScraper

        scraper = ArticleScraper(self)
        return await scraper.scrape(url)

    async def scrape_articles(
        self,
        urls: Sequence[str],
        *,
        skip_errors: bool = True,
    ) -> list[ArticleDetail]:
        """Scrape many ET article URLs.

        Args:
            urls: Sequence of absolute ET article URLs.
            skip_errors: Whether to continue when a URL fails.
        """
        from ..scrapers.article import ArticleScraper

        scraper = ArticleScraper(self)
        return await scraper.scrape_many(list(urls), skip_errors=skip_errors)


def make_sync_get(url: str, headers: dict | None = None) -> httpx.Response:
    """Perform a synchronous one-off GET for debugging and quick checks."""
    h = headers or DEFAULT_HEADERS
    with httpx.Client(headers=h, follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response
