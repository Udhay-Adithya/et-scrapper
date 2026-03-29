"""Topic/list-page scraper for Economic Times sections."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag

from ..constants import BASE_URL
from ..models import HeadlineArticle, TopicPageData
from ..utils.http import ETHttpClient


class TopicScraper:
    """Scrapes ET topic pages (for example, News/Politics/Tech list pages)."""

    def __init__(self, client: ETHttpClient):
        self.client = client

    async def scrape(self, url: str, limit: int | None = None) -> TopicPageData:
        """Fetch and parse one topic page.

        Args:
            url: Absolute topic URL.
            limit: Optional cap on number of returned articles.

        Returns:
            Parsed topic page payload with article cards.
        """
        response = await self.client.get_page(url)
        soup = BeautifulSoup(response.text, "lxml")

        schema_cards = self._parse_schema_item_list(soup)
        dom_cards = self._parse_dom_cards(soup)
        dom_meta = self._build_dom_article_meta(soup)

        merged: list[HeadlineArticle] = []
        seen: set[str] = set()

        for card in [*schema_cards, *dom_cards]:
            article_url = self._normalize_article_url(card.get("url", ""))
            title = (card.get("title") or "").strip()
            if not article_url or not title:
                continue

            if article_url in seen:
                continue
            seen.add(article_url)

            meta = dom_meta.get(article_url, {})
            merged.append(
                HeadlineArticle(
                    title=title,
                    url=article_url,
                    section=self._parse_section_name(soup),
                    summary=card.get("summary") or meta.get("summary"),
                    thumbnail_url=card.get("thumbnail_url")
                    or meta.get("thumbnail_url"),
                )
            )

            if limit and len(merged) >= limit:
                break

        return TopicPageData(
            url=url,
            section_name=self._parse_section_name(soup),
            description=self._parse_description(soup),
            scraped_at=datetime.now(timezone.utc).isoformat(),
            articles=merged,
        )

    async def scrape_many(
        self,
        urls: list[str],
        *,
        limit: int | None = None,
        skip_errors: bool = True,
    ) -> list[TopicPageData]:
        """Scrape multiple topic pages."""
        results: list[TopicPageData] = []
        for url in urls:
            try:
                results.append(await self.scrape(url, limit=limit))
            except Exception as exc:
                if not skip_errors:
                    raise
                print(f"[warn] Failed to scrape topic {url}: {exc}")
        return results

    def _parse_schema_item_list(
        self, soup: BeautifulSoup
    ) -> list[dict[str, str | None]]:
        """Extract article cards from JSON-LD ItemList scripts."""
        cards: list[dict[str, str | None]] = []

        for obj in self._json_ld_objects(soup):
            types = obj.get("@type")
            if isinstance(types, list):
                type_names = {str(t) for t in types}
            elif types is None:
                type_names = set()
            else:
                type_names = {str(types)}

            if "ItemList" not in type_names:
                continue

            elements = obj.get("itemListElement")
            if not isinstance(elements, list):
                continue

            for item in elements:
                if not isinstance(item, dict):
                    continue
                title = item.get("name")
                url = item.get("url")
                if not url and isinstance(item.get("item"), dict):
                    item_obj = item["item"]
                    url = item_obj.get("@id") or item_obj.get("url")
                    title = title or item_obj.get("name")

                if not isinstance(title, str) or not isinstance(url, str):
                    continue
                cards.append({"title": title.strip(), "url": url.strip()})

        return cards

    def _parse_dom_cards(self, soup: BeautifulSoup) -> list[dict[str, str | None]]:
        """Fallback parser that extracts article cards directly from anchors."""
        cards: list[dict[str, str | None]] = []

        for link in soup.select("a[href*='/articleshow/']"):
            href = (link.get("href") or "").strip()
            if not href:
                continue

            title = link.get_text(" ", strip=True) or (link.get("title") or "").strip()
            if not title:
                continue

            cards.append(
                {
                    "title": title,
                    "url": href,
                }
            )

        return cards

    def _build_dom_article_meta(
        self, soup: BeautifulSoup
    ) -> dict[str, dict[str, str | None]]:
        """Build a lookup of summary/thumbnail keyed by canonical article URL."""
        meta_map: dict[str, dict[str, str | None]] = {}

        for link in soup.select("a[href*='/articleshow/']"):
            href = (link.get("href") or "").strip()
            article_url = self._normalize_article_url(href)
            if not article_url:
                continue

            card = self._find_card_container(link)
            summary = None
            thumbnail_url = None

            if card:
                summary_tag = card.select_one("p.wrapLines, p, h3, h4")
                if summary_tag:
                    summary_text = summary_tag.get_text(" ", strip=True)
                    if summary_text:
                        summary = summary_text

                image_tag = card.select_one("img")
                if image_tag:
                    thumbnail_url = (
                        image_tag.get("data-original")
                        or image_tag.get("data-src")
                        or image_tag.get("src")
                    )
                    if isinstance(thumbnail_url, str):
                        thumbnail_url = thumbnail_url.strip()
                        if thumbnail_url and thumbnail_url.startswith("//"):
                            thumbnail_url = "https:" + thumbnail_url
                        elif thumbnail_url and thumbnail_url.startswith("/"):
                            thumbnail_url = urljoin(BASE_URL, thumbnail_url)

            meta_map.setdefault(
                article_url,
                {
                    "summary": summary,
                    "thumbnail_url": thumbnail_url,
                },
            )

        return meta_map

    def _find_card_container(self, link: Tag) -> Tag | None:
        """Return a likely card container around a link element."""
        class_hints = {
            "eachStory",
            "featured",
            "news-content",
            "desc",
            "story",
            "stry",
            "botplData",
            "article",
            "card",
        }

        current: Tag | None = link
        for _ in range(5):
            if not current or not isinstance(current, Tag):
                break
            if current.name in {"article", "li"}:
                return current
            classes = set(current.get("class", []))
            if classes.intersection(class_hints):
                return current
            current = current.parent if isinstance(current.parent, Tag) else None
        return None

    def _json_ld_objects(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse all JSON-LD scripts and return flattened objects."""
        objects: list[dict[str, Any]] = []

        for script in soup.select("script[type='application/ld+json']"):
            text = (script.string or script.get_text() or "").strip()
            if not text:
                continue

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, list):
                for entry in parsed:
                    if isinstance(entry, dict):
                        objects.append(entry)
            elif isinstance(parsed, dict):
                objects.append(parsed)

        return objects

    def _normalize_article_url(self, raw_url: str) -> str | None:
        """Normalize and filter ET article URLs."""
        if not raw_url:
            return None

        absolute = urljoin(BASE_URL, raw_url.strip())
        parsed = urlparse(absolute)
        path = parsed.path or ""
        host = (parsed.netloc or "").lower()

        if "/articleshow/" not in path:
            return None

        if host and host not in {"economictimes.indiatimes.com", "m.economictimes.com"}:
            return None

        canonical_host = (
            "economictimes.indiatimes.com" if host == "m.economictimes.com" else host
        )
        normalized = parsed._replace(netloc=canonical_host, query="", fragment="")
        return urlunparse(normalized)

    def _parse_section_name(self, soup: BeautifulSoup) -> str | None:
        """Extract topic page section label."""
        h1 = soup.select_one("h1")
        if h1:
            text = h1.get_text(" ", strip=True)
            if text:
                return text

        og_title = soup.select_one("meta[property='og:title']")
        if og_title and og_title.get("content"):
            raw = og_title.get("content", "").strip()
            if raw:
                return raw.split("|")[0].strip()

        title = soup.select_one("title")
        if title:
            text = title.get_text(" ", strip=True)
            if text:
                return text.split("|")[0].strip()

        return None

    def _parse_description(self, soup: BeautifulSoup) -> str | None:
        """Extract meta description for the topic page."""
        desc = soup.select_one("meta[name='description']")
        if desc and desc.get("content"):
            value = desc.get("content", "").strip()
            return value or None
        return None
