"""Detailed article scraper for Economic Times article pages."""

from __future__ import annotations

import json
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

        page_text = soup.get_text(" ", strip=True)
        page_text_lower = page_text.lower()
        has_paywall_marker_text = any(
            marker.lower() in page_text_lower for marker in PAYWALL_MARKERS[2:]
        )
        has_paywall_ui = bool(
            soup.select_one(
                "[data-paywall='true'], .prime_paywall, .paywallBox, "
                ".defaultStickyPaywallBox, .paywall_b"
            )
        )

        schema = self._parse_schema_news_article(soup)
        has_body = self._has_meaningful_body(soup, schema=schema)
        return has_paywall_marker_text and has_paywall_ui and not has_body

    async def scrape(self, url: str) -> ArticleDetail | None:
        """Fetch and parse one article.

        Args:
            url: Absolute article URL.

        Returns:
            Parsed article details, or ``None`` when paywalled.
        """
        response = await self.client.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        schema = self._parse_schema_news_article(soup)

        if self._is_paywalled(url, soup):
            return None

        return ArticleDetail(
            url=url,
            title=self._parse_title(soup, schema=schema),
            author=self._parse_author(soup, schema=schema),
            published_at=self._parse_date(soup, schema=schema),
            updated_at=self._parse_updated_date(soup, schema=schema),
            section=self._parse_section(soup, schema=schema),
            body_text=self._parse_body(soup, schema=schema),
            tags=self._parse_tags(soup, schema=schema),
            related_articles=self._parse_related(soup),
            summary=self._parse_subtitle(soup, schema=schema),
            thumbnail_url=self._parse_thumbnail(soup, schema=schema),
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

    def _parse_title(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str:
        """Extract article title from primary and fallback heading selectors."""
        if schema and isinstance(schema.get("headline"), str):
            headline = schema["headline"].strip()
            if headline:
                return headline

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

    def _parse_subtitle(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract article subtitle/summary text if available."""
        if schema and isinstance(schema.get("description"), str):
            description = schema["description"].strip()
            if description:
                return description

        for selector in [".artSub", ".article-subtitle", ".summary", "h2"]:
            tag = soup.select_one(selector)
            if tag:
                return tag.get_text(strip=True)
        return None

    def _parse_author(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract article author/byline value if present."""
        author = self._extract_author_from_schema(schema)
        if author:
            return author

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

    def _parse_date(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract a raw date string from the article page."""
        if schema and isinstance(schema.get("datePublished"), str):
            value = schema["datePublished"].strip()
            if value:
                return value

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

    def _parse_updated_date(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract an updated timestamp if present."""
        if schema and isinstance(schema.get("dateModified"), str):
            value = schema["dateModified"].strip()
            if value:
                return value

        meta = soup.select_one(
            "meta[name='Last-Modified'], meta[http-equiv='Last-Modified']"
        )
        if meta and meta.get("content"):
            value = meta.get("content", "").strip()
            return value or None
        return None

    def _parse_section(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract article section/category information."""
        if schema and isinstance(schema.get("articleSection"), str):
            section = schema["articleSection"].strip()
            if section:
                return section

        breadcrumbs = soup.select("ol.breadcrumb li a, ul.breadcrumb li a")
        if len(breadcrumbs) >= 2:
            return breadcrumbs[-1].get_text(strip=True)
        tag = soup.select_one("[class*='section'], [class*='category']")
        return tag.get_text(strip=True) if tag else None

    def _parse_body(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str:
        """Extract and join article body paragraphs."""
        if schema and isinstance(schema.get("articleBody"), str):
            raw = schema["articleBody"].strip()
            if raw:
                text = self._normalize_schema_body(raw)
                if text:
                    return text

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

    def _parse_tags(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> List[str]:
        """Extract article tags and deduplicate while preserving order."""
        tags: List[str] = []

        if schema:
            keywords = schema.get("keywords")
            if isinstance(keywords, str):
                tags.extend([k.strip() for k in keywords.split(",") if k.strip()])
            elif isinstance(keywords, list):
                tags.extend([str(k).strip() for k in keywords if str(k).strip()])

        for meta_tag in soup.select("meta[property='article:tag']"):
            value = (meta_tag.get("content") or "").strip()
            if value:
                tags.append(value)

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

    def _parse_thumbnail(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> str | None:
        """Extract the best-available article thumbnail URL."""
        if schema:
            image = schema.get("image")
            if isinstance(image, dict) and isinstance(image.get("url"), str):
                return image.get("url")
            if isinstance(image, list):
                for entry in image:
                    if isinstance(entry, str) and entry.strip():
                        return entry.strip()
                    if isinstance(entry, dict) and isinstance(entry.get("url"), str):
                        return entry.get("url")
            if isinstance(image, str) and image.strip():
                return image.strip()

        tag = soup.select_one("meta[property='og:image']")
        if tag and tag.get("content"):
            return tag.get("content")
        image_tag = soup.select_one("article img, div.artText img")
        return image_tag.get("src") if image_tag else None

    def _parse_schema_news_article(self, soup: BeautifulSoup) -> dict | None:
        """Extract the most relevant NewsArticle object from JSON-LD scripts."""
        for script in soup.select("script[type='application/ld+json']"):
            text = (script.string or script.get_text() or "").strip()
            if not text:
                continue

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue

            candidates = parsed if isinstance(parsed, list) else [parsed]
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                type_name = candidate.get("@type")
                if type_name == "NewsArticle":
                    return candidate
                if isinstance(type_name, list) and "NewsArticle" in type_name:
                    return candidate
        return None

    def _extract_author_from_schema(self, schema: dict | None) -> str | None:
        """Extract author text from schema author object/array/string."""
        if not schema:
            return None
        raw = schema.get("author")
        if isinstance(raw, dict):
            name = raw.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        if isinstance(raw, list):
            names: list[str] = []
            for entry in raw:
                if isinstance(entry, dict):
                    name = entry.get("name")
                    if isinstance(name, str) and name.strip():
                        names.append(name.strip())
                elif isinstance(entry, str) and entry.strip():
                    names.append(entry.strip())
            if names:
                return ", ".join(dict.fromkeys(names))
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return None

    def _normalize_schema_body(self, raw: str) -> str:
        """Normalize schema articleBody text into paragraph-like formatting."""
        collapsed = " ".join(raw.split())
        return collapsed

    def _has_meaningful_body(
        self,
        soup: BeautifulSoup,
        *,
        schema: dict | None = None,
    ) -> bool:
        """Return True when the page has a substantial article body."""
        if schema and isinstance(schema.get("articleBody"), str):
            if len(schema["articleBody"].strip()) >= 240:
                return True

        body = soup.select_one("div.artText, div[class*='article-body'], article")
        if body and len(body.get_text(" ", strip=True)) >= 240:
            return True
        return False
