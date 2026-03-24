"""Public package API for the ET scraper.

Example:

::

    async with ETHttpClient() as client:
    homepage = await client.scrape_homepage()
    articles = await client.scrape_articles(urls)
"""

from __future__ import annotations

from .models import ArticleDetail, HomepageData
from .utils.http import ETHttpClient


async def scrape_homepage() -> HomepageData:
    """Scrape ET homepage data using a temporary client context."""
    async with ETHttpClient() as client:
        return await client.scrape_homepage()


async def scrape_articles(
    urls: list[str], skip_errors: bool = True
) -> list[ArticleDetail]:
    """Scrape many ET article URLs using a temporary client context."""
    async with ETHttpClient() as client:
        return await client.scrape_articles(urls, skip_errors=skip_errors)


__all__ = [
    "ETHttpClient",
    "HomepageData",
    "ArticleDetail",
    "scrape_homepage",
    "scrape_articles",
]
