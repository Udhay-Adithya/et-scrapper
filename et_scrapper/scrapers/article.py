"""Detailed article scraper for Economic Times article pages."""

from __future__ import annotations

from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..constants import BASE_URL, PAYWALL_MARKERS, RELATED_ARTICLES_LIMIT
from ..models import ArticleDetail, HeadlineArticle
from ..utils.http import ETHttpClient


class ArticleScraper:
    """Scrapes individual ET article pages.

    Args:
        client: Initialised asynchronous HTTP client.
    """

    def __init__(self, client: ETHttpClient):
        """Store a shared HTTP client used for article requests.

        Args:
            client: Initialised asynchronous HTTP client.
        """
        self.client = client

    def _is_paywalled(self, url: str, soup: BeautifulSoup) -> bool:
        """Return True if the article appears to be behind the ETPrime paywall."""
        if any(marker.lower() in url.lower() for marker in PAYWALL_MARKERS):
            return True
        page_text = soup.get_text()
        return any(marker in page_text for marker in PAYWALL_MARKERS[2:])

    async def scrape(self, url: str) -> ArticleDetail | None:
        """Fetch and parse one article.

        Args:
            url: Absolute article URL.

        Returns:
            Parsed article details, or ``None`` when paywalled.
        """
        response = await self.client.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        if self._is_paywalled(url, soup):
            return None

        return ArticleDetail(
            url=url,
            title=self._parse_title(soup),
            author=self._parse_author(soup),
            published_at=self._parse_date(soup),
            section=self._parse_section(soup),
            body_text=self._parse_body(soup),
            tags=self._parse_tags(soup),
            related_articles=self._parse_related(soup),
            summary=self._parse_subtitle(soup),
            thumbnail_url=self._parse_thumbnail(soup),
        )

    async def scrape_many(
        self, urls: List[str], skip_errors: bool = True
    ) -> List[ArticleDetail]:
        """Scrape multiple article URLs.

        Args:
            urls: List of absolute article URLs.
            skip_errors: If ``True``, invalid/failed URLs are skipped.

        Returns:
            A list of successfully parsed, non-paywalled articles.
        """
        results: List[ArticleDetail] = []
        for url in urls:
            try:
                article = await self.scrape(url)
                if article is not None:
                    results.append(article)
            except Exception as exc:
                if not skip_errors:
                    raise
                print(f"[warn] Failed to scrape {url}: {exc}")
        return results

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from primary and fallback heading selectors."""
        # Canonical title selectors for ET article pages
        for selector in [
            "h1.artTitle",
            "h1[class*='article']",
            "h1[class*='title']",
            "h1",
        ]:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return ""

    def _parse_subtitle(self, soup: BeautifulSoup) -> str | None:
        """Extract article subtitle/summary text if available."""
        for selector in [".artSub", ".article-subtitle", ".summary", "h2"]:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return None

    def _parse_author(self, soup: BeautifulSoup) -> str | None:
        """Extract article author/byline value if present."""
        for selector in [
            ".artAuthor",
            "[class*='author']",
            "[class*='byline']",
            "span.writer",
        ]:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return None

    def _parse_date(self, soup: BeautifulSoup) -> str | None:
        """Extract a raw date string from the article page."""
        # Try <time> element first
        time_tag = soup.select_one("time[datetime]")
        if time_tag:
            return time_tag.get("datetime")

        # Fall back to text in date-like spans
        for selector in [".publish-date", ".artDate", ".date", ".time"]:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return None

    def _parse_section(self, soup: BeautifulSoup) -> str | None:
        """Extract article section/category information."""
        breadcrumbs = soup.select("ol.breadcrumb li a, ul.breadcrumb li a")
        if len(breadcrumbs) >= 2:
            return breadcrumbs[-1].get_text(strip=True)
        tag = soup.select_one("[class*='section'], [class*='category']")
        return tag.get_text(strip=True) if tag else None

    def _parse_body(self, soup: BeautifulSoup) -> str:
        """Extract and join article body paragraphs."""
        # ET article bodies live in these containers
        container = soup.select_one(
            "div.artText, div[class*='article-body'], "
            "div[class*='artBody'], div.story-content"
        )
        if container:
            paragraphs = container.find_all("p")
        else:
            # Broad fallback
            paragraphs = soup.find_all("p")

        texts = [
            p.get_text(" ", strip=True) for p in paragraphs if p.get_text(strip=True)
        ]
        return "\n\n".join(texts)

    def _parse_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags and deduplicate while preserving order."""
        tags: List[str] = []
        for tag in soup.select("div.tags a, ul.article-tags li a, [class*='tag'] a"):
            text = tag.get_text(strip=True)
            if text:
                tags.append(text)
        return list(dict.fromkeys(tags))  # deduplicate, preserve order

    def _parse_related(self, soup: BeautifulSoup) -> List[HeadlineArticle]:
        """Extract related article cards from article detail pages."""
        related: List[HeadlineArticle] = []
        for tag in soup.select(
            "div.related-stories a, ul.related li a, " "div[class*='related'] a"
        ):
            title = tag.get_text(strip=True)
            href = tag.get("href", "")
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            if title:
                related.append(HeadlineArticle(title=title, url=href))
        return related[:RELATED_ARTICLES_LIMIT]

    def _parse_thumbnail(self, soup: BeautifulSoup) -> str | None:
        """Extract the best-available article thumbnail URL."""
        tag = soup.select_one("meta[property='og:image']")
        if tag and tag.get("content"):
            return tag.get("content")
        image_tag = soup.select_one("article img, div.artText img")
        return image_tag.get("src") if image_tag else None
