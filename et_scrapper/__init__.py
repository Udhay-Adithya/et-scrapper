"""Public package API for the ET scraper.

Example:

::

    async with ETHttpClient() as client:
    homepage = await client.scrape_homepage()
    articles = await client.scrape_articles(urls)
"""

from __future__ import annotations

from .models import ArticleDetail, HomepageData, TopicPageData
from .utils.http import ETHttpClient


async def scrape_homepage() -> HomepageData:
    """Scrape ET homepage data using a temporary client context.

    Returns:
        HomepageData: Parsed homepage payload.
    """
    async with ETHttpClient() as client:
        return await client.scrape_homepage()


async def scrape_articles(
    urls: list[str], skip_errors: bool = True
) -> list[ArticleDetail]:
    """Scrape many ET article URLs using a temporary client context.

    Args:
        urls: Absolute ET article URLs to scrape.
        skip_errors: Whether to continue when one URL fails.

    Returns:
        list[ArticleDetail]: Parsed article details.
    """
    async with ETHttpClient() as client:
        return await client.scrape_articles(urls, skip_errors=skip_errors)


async def scrape_topic_page(url: str, limit: int | None = None) -> TopicPageData:
    """Scrape one ET topic/list page using a temporary client context.

    Args:
        url: Absolute topic/list page URL.
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed topic/list page data.
    """
    async with ETHttpClient() as client:
        return await client.scrape_topic_page(url, limit=limit)


async def scrape_topic_pages(
    urls: list[str],
    *,
    limit: int | None = None,
    skip_errors: bool = True,
) -> list[TopicPageData]:
    """Scrape many ET topic/list pages using a temporary client context.

    Args:
        urls: Absolute topic/list page URLs.
        limit: Optional cap applied per page.
        skip_errors: Whether to continue when one URL fails.

    Returns:
        list[TopicPageData]: Parsed topic/list page payloads.
    """
    async with ETHttpClient() as client:
        return await client.scrape_topic_pages(
            urls,
            limit=limit,
            skip_errors=skip_errors,
        )


async def scrape_trending_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Trending/Updates topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed trending page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_trending_news(limit=limit)


async def scrape_india_news(limit: int | None = None) -> TopicPageData:
    """Scrape the India news topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed India page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_india_news(limit=limit)


async def scrape_economy_finance_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Economy/Finance topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed economy/finance page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_economy_finance_news(limit=limit)


async def scrape_politics_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Politics topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed politics page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_politics_news(limit=limit)


async def scrape_sports_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Sports topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed sports page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_sports_news(limit=limit)


async def scrape_tech_internet_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Tech and Internet topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed technology page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_tech_internet_news(limit=limit)


async def scrape_stock_market_news(limit: int | None = None) -> TopicPageData:
    """Scrape the Stocks news topic page.

    Args:
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed stocks news page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_stock_market_news(limit=limit)


async def scrape_topic_search_news(
    topic: str,
    *,
    limit: int | None = None,
) -> TopicPageData:
    """Scrape a topic search route generated from free-form topic text.

    Args:
        topic: Topic string mapped to ``/topic/<slug>/news``.
        limit: Optional cap on returned article cards.

    Returns:
        TopicPageData: Parsed topic-search page.
    """
    async with ETHttpClient() as client:
        return await client.scrape_topic_search_news(topic, limit=limit)


async def scrape_curated_topic_pages(
    *,
    limit: int | None = None,
    skip_errors: bool = True,
) -> list[TopicPageData]:
    """Scrape all built-in curated topic pages with one call.

    Args:
        limit: Optional cap applied per topic page.
        skip_errors: Whether to continue on per-page failures.

    Returns:
        list[TopicPageData]: Parsed curated topic pages.
    """
    async with ETHttpClient() as client:
        return await client.scrape_curated_topic_pages(
            limit=limit,
            skip_errors=skip_errors,
        )


__all__ = [
    "ETHttpClient",
    "HomepageData",
    "ArticleDetail",
    "TopicPageData",
    "scrape_homepage",
    "scrape_articles",
    "scrape_topic_page",
    "scrape_topic_pages",
    "scrape_trending_news",
    "scrape_india_news",
    "scrape_economy_finance_news",
    "scrape_politics_news",
    "scrape_sports_news",
    "scrape_tech_internet_news",
    "scrape_stock_market_news",
    "scrape_topic_search_news",
    "scrape_curated_topic_pages",
]
