"""Homepage scraper for Economic Times.

The scraper focuses on broad CSS selectors with fallbacks so that moderate
layout changes on ET do not immediately break extraction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from bs4 import BeautifulSoup

from ..models import (
    HeadlineArticle,
    MarketIndex,
    StockQuote,
    CryptoPrice,
    MutualFund,
    SectionArticle,
    NewsSection,
    OpinionArticle,
    VideoItem,
    HomepageData,
)
from ..constants import BASE_URL, TOP_STORIES_LIMIT
from ..utils.http import ETHttpClient


class HomepageScraper:
    """Scrapes the Economic Times homepage into strongly-typed models.

    Args:
        client: Initialised asynchronous HTTP client.
    """

    def __init__(self, client: ETHttpClient):
        """Store a shared HTTP client used for homepage requests.

        Args:
            client: Initialised asynchronous HTTP client.
        """
        self.client = client

    async def scrape(self) -> HomepageData:
        """Fetch and parse the homepage.

        Returns:
            A fully populated :class:`HomepageData` object.
        """
        response = await self.client.get_page("/", delay=False)
        soup = BeautifulSoup(response.text, "lxml")

        return HomepageData(
            scraped_at=datetime.now(timezone.utc).isoformat(),
            headlines=self._parse_top_stories(soup),
            market_indices=self._parse_market_benchmarks(soup),
            top_stocks=self._parse_stocks(soup),
            crypto_prices=self._parse_crypto(soup),
            mutual_funds=self._parse_mutual_funds(soup),
            news_sections=self._parse_news_sections(soup),
            opinion_articles=self._parse_opinions(soup),
            videos=self._parse_videos(soup),
        )

    # ------------------------------------------------------------------
    # Top Stories
    # ------------------------------------------------------------------
    def _parse_top_stories(self, soup: BeautifulSoup) -> List[HeadlineArticle]:
        """Extract top stories from current homepage headline widgets."""
        articles: List[HeadlineArticle] = []
        seen: set[str] = set()

        # Primary top stories block in current Next.js markup.
        for tag in soup.select("#topStories li.storyItem, #topStories li"):
            title_tag = tag.select_one("h1 a, a.newsTitle, a[href]")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")
            if not title or not url:
                continue
            if url and not url.startswith("http"):
                url = BASE_URL + url
            key = url or title
            if key in seen:
                continue
            seen.add(key)

            summary_tag = tag.select_one("p, h2, h3")
            summary = summary_tag.get_text(strip=True) if summary_tag else None
            img_tag = tag.select_one("img")
            image_url = img_tag.get("src") if img_tag else None
            articles.append(
                HeadlineArticle(
                    title=title,
                    url=url,
                    summary=summary,
                    thumbnail_url=image_url,
                    section="Top Stories",
                )
            )

        # Secondary top-news list widget.
        if len(articles) < TOP_STORIES_LIMIT:
            for tag in soup.select("div.tabsContent ul.newsList li"):
                title_tag = tag.select_one("a[href]")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                url = title_tag.get("href", "")
                if not title or not url:
                    continue
                if url and not url.startswith("http"):
                    url = BASE_URL + url
                key = url or title
                if key in seen:
                    continue
                seen.add(key)
                articles.append(
                    HeadlineArticle(
                        title=title,
                        url=url,
                        summary=None,
                        thumbnail_url=None,
                        section="Top News",
                    )
                )

        # Generic heading fallback.
        if not articles:
            for tag in soup.select("h1 a, h2 a"):
                title = tag.get_text(strip=True)
                url = tag.get("href", "")
                if url and not url.startswith("http"):
                    url = BASE_URL + url
                if title:
                    articles.append(
                        HeadlineArticle(title=title, url=url, section="Top Stories")
                    )

        return articles[:TOP_STORIES_LIMIT]

    # ------------------------------------------------------------------
    # Market Benchmarks (top ticker: Sensex, Nifty, etc.)
    # ------------------------------------------------------------------
    def _parse_market_benchmarks(self, soup: BeautifulSoup) -> List[MarketIndex]:
        """Extract ET markets headlines into benchmark slots.

        ET's current homepage no longer exposes stable numeric ticker rows in
        static HTML. As a fallback, this parser captures the ET Markets widget
        headlines so callers still receive market-context items.
        """
        benchmarks: List[MarketIndex] = []

        for item in soup.select(
            "li.etMarkets ul.newsList li, .etMarkets ul.newsList li"
        ):
            name_tag = item.select_one("a[href]")
            name = (
                name_tag.get_text(strip=True) if name_tag else item.get_text(strip=True)
            )
            if not name:
                continue
            benchmarks.append(MarketIndex(name=name))

        return benchmarks

    # ------------------------------------------------------------------
    # Stocks
    # ------------------------------------------------------------------
    def _parse_stocks(self, soup: BeautifulSoup) -> List[StockQuote]:
        """Extract stock quote rows from stock widgets and tables."""
        stocks: List[StockQuote] = []

        for row in soup.select("table.stock-table tr, div.stock-list div.stock-row"):
            cells = row.select("td")
            if len(cells) < 3:
                continue
            try:
                symbol = cells[0].get_text(strip=True)
                price = float(cells[1].get_text(strip=True).replace(",", ""))
                change_text = cells[2].get_text(strip=True).replace(",", "")
                change = float(change_text) if change_text else None
                pct_text = (
                    cells[3].get_text(strip=True).replace("%", "")
                    if len(cells) > 3
                    else None
                )
                pct = float(pct_text) if pct_text else None
                stocks.append(
                    StockQuote(name=symbol, price=price, change=change, change_pct=pct)
                )
            except (ValueError, IndexError):
                continue

        return stocks

    # ------------------------------------------------------------------
    # Crypto
    # ------------------------------------------------------------------
    def _parse_crypto(self, soup: BeautifulSoup) -> List[CryptoPrice]:
        """Extract crypto rows from the homepage crypto-news slider."""
        crypto_list: List[CryptoPrice] = []
        seen: set[str] = set()

        for item in soup.select(".cryptoNewsContainer a.newsCardWrapper"):
            name_tag = item.select_one("h3.newsTitle, h3, .newsTitle")
            name = name_tag.get_text(strip=True) if name_tag else None
            if not name:
                continue
            symbol = "".join(ch for ch in name[:5].upper() if ch.isalpha()) or "CRYP"
            key = f"{symbol}:{name}"
            if key in seen:
                continue
            seen.add(key)

            crypto_list.append(
                CryptoPrice(
                    name=name,
                    symbol=symbol,
                    price_inr=None,
                    change_pct=None,
                )
            )

        return crypto_list

    # ------------------------------------------------------------------
    # Mutual Funds
    # ------------------------------------------------------------------
    def _parse_mutual_funds(self, soup: BeautifulSoup) -> List[MutualFund]:
        """Extract mutual fund cards and rows from available sections."""
        funds: List[MutualFund] = []

        for row in soup.select("div.mf-list li, table.mf-table tr"):
            name_tag = row.select_one(".name, a")
            nav_tag = row.select_one(".nav, .price")
            ret_tag = row.select_one(".return, .returns, .percent")

            name = name_tag.get_text(strip=True) if name_tag else None
            if not name:
                continue
            try:
                nav = (
                    float(nav_tag.get_text(strip=True).replace(",", ""))
                    if nav_tag
                    else None
                )
            except ValueError:
                nav = None
            try:
                ret_1y = (
                    float(ret_tag.get_text(strip=True).replace("%", ""))
                    if ret_tag
                    else None
                )
            except ValueError:
                ret_1y = None

            funds.append(MutualFund(name=name, fund_size_cr=nav, return_1y=ret_1y))

        return funds

    # ------------------------------------------------------------------
    # Categorized News Sections
    # ------------------------------------------------------------------
    def _parse_news_sections(self, soup: BeautifulSoup) -> List[NewsSection]:
        """Extract grouped news widgets where each widget has multiple links."""
        sections: List[NewsSection] = []
        seen_sections: set[str] = set()

        # Top news tabs widget.
        for section_div in soup.select("div.tabsContent"):
            heading_tag = section_div.find_previous("div", class_="tabs")
            tab = heading_tag.select_one(".tab.active") if heading_tag else None
            section_name = tab.get_text(strip=True) if tab else "Top News"

            articles: List[SectionArticle] = []
            for link in section_div.select("ul.newsList li a[href]"):
                title = link.get_text(strip=True)
                url = link.get("href", "")
                if url and not url.startswith("http"):
                    url = BASE_URL + url
                if title:
                    articles.append(
                        SectionArticle(title=title, url=url, section=section_name)
                    )

            if articles and section_name not in seen_sections:
                seen_sections.add(section_name)
                sections.append(
                    NewsSection(section_name=section_name, articles=articles)
                )

        # Center list widget cards.
        for section_div in soup.select(".newsListContainer"):
            heading_tag = section_div.find_previous(["h2", "h3"])
            section_name = heading_tag.get_text(strip=True) if heading_tag else "News"

            articles: List[SectionArticle] = []
            for link in section_div.select(".newsListItem a[href]"):
                title = link.get_text(strip=True)
                url = link.get("href", "")
                if url and not url.startswith("http"):
                    url = BASE_URL + url
                if title:
                    articles.append(
                        SectionArticle(title=title, url=url, section=section_name)
                    )

            if articles and section_name not in seen_sections:
                seen_sections.add(section_name)
                sections.append(
                    NewsSection(section_name=section_name, articles=articles)
                )

        # ET markets mini list.
        market_links = []
        for link in soup.select(".etMarkets ul.newsList li a[href]"):
            title = link.get_text(strip=True)
            url = link.get("href", "")
            if url and not url.startswith("http"):
                url = BASE_URL + url
            if title:
                market_links.append(
                    SectionArticle(title=title, url=url, section="ET Markets")
                )
        if market_links and "ET Markets" not in seen_sections:
            seen_sections.add("ET Markets")
            sections.append(
                NewsSection(section_name="ET Markets", articles=market_links)
            )

        return sections

    # ------------------------------------------------------------------
    # Opinion / Expert Views
    # ------------------------------------------------------------------
    def _parse_opinions(self, soup: BeautifulSoup) -> List[OpinionArticle]:
        """Extract opinion and expert-view article links."""
        opinions: List[OpinionArticle] = []

        for item in soup.select("section.opinionWidget article.opinionItem"):
            title_tag = item.select_one("a.opinionTitle, a[href]")
            author_tags = item.select(".opinionAuthor")
            author_tag = author_tags[-1] if author_tags else None

            title = (
                title_tag.get_text(strip=True)
                if title_tag
                else item.get_text(strip=True)
            )
            url = title_tag.get("href", "") if title_tag else ""
            if url and not url.startswith("http"):
                url = BASE_URL + url
            author = author_tag.get_text(strip=True) if author_tag else None

            if title:
                opinions.append(
                    OpinionArticle(
                        title=title,
                        url=url,
                        author_name=author,
                        section="Opinion",
                    )
                )

        return opinions

    # ------------------------------------------------------------------
    # Videos
    # ------------------------------------------------------------------
    def _parse_videos(self, soup: BeautifulSoup) -> List[VideoItem]:
        """Extract video cards including title, link, and thumbnail metadata."""
        videos: List[VideoItem] = []
        seen: set[str] = set()

        for item in soup.select(
            "section.videos .rhsRelV ul.newsList li, #topStories li.storyItem"
        ):
            title_tag = item.select_one("a[href*='videoshow'], a[href]")
            thumb_tag = item.select_one("img")
            dur_tag = item.select_one(".duration, .dur")

            title = title_tag.get_text(strip=True) if title_tag else None
            if not title:
                continue
            url = (
                title_tag.get("href", "") if title_tag and title_tag.name == "a" else ""
            )
            if url and not url.startswith("http"):
                url = BASE_URL + url
            if not url:
                continue
            key = url
            if key in seen:
                continue
            seen.add(key)
            thumbnail = thumb_tag.get("src") if thumb_tag else None
            duration = dur_tag.get_text(strip=True) if dur_tag else None

            videos.append(
                VideoItem(
                    title=title,
                    url=url,
                    thumbnail_url=thumbnail,
                    duration=duration,
                )
            )

        return videos
