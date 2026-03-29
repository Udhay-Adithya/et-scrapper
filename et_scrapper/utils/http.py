"""HTTP client utilities for ET scraper with anti-detection headers."""

import asyncio
import random
import re
from typing import Optional, Sequence

import httpx

from ..constants import (
    BASE_URL,
    DEFAULT_HEADERS,
    DEFAULT_TOPIC_KEYS,
    MAX_DELAY_SECONDS,
    MIN_DELAY_SECONDS,
    TOPIC_PATHS,
)
from ..models import ArticleDetail, HomepageData, TopicPageData


class ETHttpClient:
    """Asynchronous HTTP client and high-level API for ET scraping.

    Typical usage:

    ::

        async with ETHttpClient() as client:
            homepage = await client.scrape_homepage()
            articles = await client.scrape_articles(["https://..."])

    Args:
        headers: Optional custom HTTP headers.
        timeout: Request timeout in seconds.
        follow_redirects: Whether redirects should be followed.

    Notes:
        This client is designed to be used as an async context manager so that
        network connections are opened and closed deterministically.
    """

    def __init__(
        self,
        headers: Optional[dict] = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ):
        """Initialize HTTP client configuration.

        Args:
            headers: Optional custom HTTP headers. If omitted, package defaults
                are used.
            timeout: Request timeout in seconds for connect/read/write phases.
            follow_redirects: Whether HTTP redirects should be followed.
        """
        self.headers = headers or DEFAULT_HEADERS
        self.timeout = httpx.Timeout(timeout)
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ETHttpClient":
        """Create and open the underlying async HTTP client.

        Returns:
            ETHttpClient: The same client instance for fluent ``async with`` use.
        """
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Close the underlying HTTP client when leaving context.

        Args:
            *args: Standard async context-manager exit tuple
                ``(exc_type, exc, traceback)``.
        """
        if self._client:
            await self._client.aclose()

    async def _random_delay(self) -> None:
        """Sleep for a randomized interval to reduce bursty traffic.

        The delay window is controlled by ``MIN_DELAY_SECONDS`` and
        ``MAX_DELAY_SECONDS`` constants.
        """
        delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        await asyncio.sleep(delay)

    async def get(self, url: str, delay: bool = True) -> httpx.Response:
        """Perform a GET request with optional pre-request throttling.

        Args:
            url: Absolute URL to request.
            delay: Whether to sleep for a randomized anti-burst delay before
                making the request.

        Returns:
            httpx.Response: Successful HTTP response object.

        Raises:
            RuntimeError: If called before the async client is initialized.
            httpx.HTTPStatusError: If the server returns a non-2xx status code.
            httpx.HTTPError: For transport-level request failures.
        """
        if self._client is None:
            raise RuntimeError("Client not initialised. Use async context manager.")
        if delay:
            await self._random_delay()
        response = await self._client.get(url)
        response.raise_for_status()
        return response

    async def get_page(self, path: str = "", delay: bool = True) -> httpx.Response:
        """Fetch an ET page by relative path or absolute URL.

        Args:
            path: Relative path like ``/news/india`` or an absolute URL.
            delay: Whether to apply pre-request random delay.

        Returns:
            httpx.Response: Successful HTTP response object.
        """
        url = BASE_URL + path if not path.startswith("http") else path
        return await self.get(url, delay=delay)

    async def scrape_homepage(self) -> HomepageData:
        """Scrape the ET homepage into the typed homepage model.

        Returns:
            HomepageData: Parsed homepage payload containing headlines,
            markets, sections, videos, and related entities.
        """
        from ..scrapers.homepage import HomepageScraper

        scraper = HomepageScraper(self)
        return await scraper.scrape()

    async def scrape_article(self, url: str) -> ArticleDetail | None:
        """Scrape one ET article URL into a typed detail model.

        Args:
            url: Absolute ET article URL.

        Returns:
            ArticleDetail | None: Parsed article data, or ``None`` for
            inaccessible/paywalled pages.
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

        Returns:
            list[ArticleDetail]: Parsed, non-null article detail objects.
        """
        from ..scrapers.article import ArticleScraper

        scraper = ArticleScraper(self)
        return await scraper.scrape_many(list(urls), skip_errors=skip_errors)

    async def scrape_topic_page(
        self,
        url: str,
        *,
        limit: int | None = None,
    ) -> TopicPageData:
        """Scrape one ET topic/list page.

        Args:
            url: Absolute topic page URL.
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Structured topic page data with normalized card list.
        """
        from ..scrapers.topic import TopicScraper

        scraper = TopicScraper(self)
        return await scraper.scrape(url, limit=limit)

    async def scrape_topic_pages(
        self,
        urls: Sequence[str],
        *,
        limit: int | None = None,
        skip_errors: bool = True,
    ) -> list[TopicPageData]:
        """Scrape multiple ET topic/list pages.

        Args:
            urls: Sequence of absolute topic/list URLs.
            limit: Optional cap applied per topic page.
            skip_errors: Whether to continue scraping remaining URLs if one
                URL fails.

        Returns:
            list[TopicPageData]: Parsed topic pages in input order.
        """
        from ..scrapers.topic import TopicScraper

        scraper = TopicScraper(self)
        return await scraper.scrape_many(
            list(urls),
            limit=limit,
            skip_errors=skip_errors,
        )

    def _topic_url(self, key: str) -> str:
        """Resolve a configured topic key to an absolute URL.

        Args:
            key: Key present in ``TOPIC_PATHS``.

        Returns:
            str: Fully qualified topic URL.

        Raises:
            ValueError: If the provided key is not configured.
        """
        try:
            path = TOPIC_PATHS[key]
        except KeyError as exc:
            valid = ", ".join(sorted(TOPIC_PATHS.keys()))
            raise ValueError(f"Unknown topic key: {key}. Valid keys: {valid}") from exc
        return BASE_URL + path

    async def scrape_trending_news(self, *, limit: int | None = None) -> TopicPageData:
        """Scrape the Trending/Updates topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed trending updates page.
        """
        return await self.scrape_topic_page(self._topic_url("trending"), limit=limit)

    async def scrape_india_news(self, *, limit: int | None = None) -> TopicPageData:
        """Scrape the India news topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed India topic page.
        """
        return await self.scrape_topic_page(self._topic_url("india"), limit=limit)

    async def scrape_economy_finance_news(
        self,
        *,
        limit: int | None = None,
    ) -> TopicPageData:
        """Scrape the Economy/Finance topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed Economy/Finance topic page.
        """
        return await self.scrape_topic_page(
            self._topic_url("economy_finance"),
            limit=limit,
        )

    async def scrape_politics_news(self, *, limit: int | None = None) -> TopicPageData:
        """Scrape the Politics topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed Politics topic page.
        """
        return await self.scrape_topic_page(self._topic_url("politics"), limit=limit)

    async def scrape_sports_news(self, *, limit: int | None = None) -> TopicPageData:
        """Scrape the Sports topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed Sports topic page.
        """
        return await self.scrape_topic_page(self._topic_url("sports"), limit=limit)

    async def scrape_tech_internet_news(
        self,
        *,
        limit: int | None = None,
    ) -> TopicPageData:
        """Scrape the Tech and Internet topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed technology topic page.
        """
        return await self.scrape_topic_page(
            self._topic_url("tech_internet"), limit=limit
        )

    async def scrape_stock_market_news(
        self,
        *,
        limit: int | None = None,
    ) -> TopicPageData:
        """Scrape the Stocks news topic page.

        Args:
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed stocks news topic page.
        """
        return await self.scrape_topic_page(self._topic_url("stocks_news"), limit=limit)

    def _search_topic_url(self, topic: str) -> str:
        """Build a ``/topic/<keyword>/news`` URL from a free-form string.

        Args:
            topic: Free-form topic phrase like ``"Andhra Pradesh"`` or
                ``"stock-market"``.

        Returns:
            str: Absolute ET search-topic URL.

        Raises:
            ValueError: If normalization yields an empty slug.
        """
        normalized = topic.strip().lower().replace("_", " ").replace("-", " ")
        normalized = re.sub(r"\s+", "-", normalized)
        slug = re.sub(r"[^a-z0-9-]", "", normalized).strip("-")
        if not slug:
            raise ValueError("Topic must contain at least one alphanumeric character.")
        return f"{BASE_URL}/topic/{slug}/news"

    async def scrape_topic_search_news(
        self,
        topic: str,
        *,
        limit: int | None = None,
    ) -> TopicPageData:
        """Scrape a topic search route generated from a topic string.

        Args:
            topic: Input topic used to generate ``/topic/<slug>/news``.
            limit: Optional cap on returned article cards.

        Returns:
            TopicPageData: Parsed topic-search page.
        """
        return await self.scrape_topic_page(self._search_topic_url(topic), limit=limit)

    async def scrape_curated_topic_pages(
        self,
        *,
        limit: int | None = None,
        skip_errors: bool = True,
    ) -> list[TopicPageData]:
        """Scrape all built-in curated topic pages in one call.

        Args:
            limit: Optional cap applied per topic page.
            skip_errors: Whether to continue on individual page failures.

        Returns:
            list[TopicPageData]: Parsed topic pages for keys in
            ``DEFAULT_TOPIC_KEYS``.
        """
        urls = [self._topic_url(key) for key in DEFAULT_TOPIC_KEYS]
        return await self.scrape_topic_pages(
            urls,
            limit=limit,
            skip_errors=skip_errors,
        )


def make_sync_get(url: str, headers: dict | None = None) -> httpx.Response:
    """Perform a synchronous one-off GET request.

    This helper is intended for quick debugging scripts where async client
    setup would be unnecessary.

    Args:
        url: Absolute URL to fetch.
        headers: Optional custom headers. Uses package defaults when omitted.

    Returns:
        httpx.Response: Successful HTTP response object.

    Raises:
        httpx.HTTPStatusError: If the server returns a non-2xx status code.
        httpx.HTTPError: For transport-level request failures.
    """
    h = headers or DEFAULT_HEADERS
    with httpx.Client(headers=h, follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response
