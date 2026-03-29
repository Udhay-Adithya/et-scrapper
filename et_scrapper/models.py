"""Pydantic models used by the Economic Times scraper package.

These models define the public data contract returned by function-based APIs,
and scraper classes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HeadlineArticle(BaseModel):
    """Represents a top-story or headline card shown on the homepage."""

    title: str
    url: str
    section: str | None = None
    thumbnail_url: str | None = None
    summary: str | None = None
    is_live_blog: bool = False


class MarketIndex(BaseModel):
    """Represents an index ticker row, such as Nifty 50 or Sensex."""

    name: str
    value: float | None = None
    change: float | None = None
    change_pct: float | None = None
    status: str = "UNKNOWN"


class StockQuote(BaseModel):
    """Represents a stock quote item listed on homepage market widgets."""

    name: str
    url: str | None = None
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    timestamp: str | None = None


class TopGainerLoser(BaseModel):
    """Represents a top-gainer or top-loser stock row."""

    name: str
    ticker: str | None = None
    url: str | None = None
    price: float | None = None
    change_pct: float | None = None
    market: str = "NSE"


class CryptoPrice(BaseModel):
    """Represents a cryptocurrency quote extracted from homepage widgets."""

    name: str
    symbol: str
    url: str | None = None
    price_inr: float | None = None
    change_pct: float | None = None


class MutualFund(BaseModel):
    """Represents a mutual fund card or row from ET mutual-fund sections."""

    name: str
    url: str | None = None
    category: str | None = None
    star_rating: int | None = None
    fund_size_cr: float | None = None
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_3y: float | None = None
    return_5y: float | None = None
    is_featured: bool = False


class SectionArticle(BaseModel):
    """Represents a single article inside a categorized homepage section."""

    title: str
    url: str
    section: str
    thumbnail_url: str | None = None
    summary: str | None = None
    author: str | None = None


class NewsSection(BaseModel):
    """Represents a grouped homepage section with multiple article cards."""

    section_name: str
    section_url: str | None = None
    articles: list[SectionArticle] = Field(default_factory=list)


class OpinionArticle(BaseModel):
    """Represents an opinion or expert-view article card."""

    title: str
    url: str
    author_name: str | None = None
    author_role: str | None = None
    author_org: str | None = None
    author_image_url: str | None = None
    section: str = "Opinion"


class VideoItem(BaseModel):
    """Represents a homepage video card."""

    title: str
    url: str
    thumbnail_url: str | None = None
    duration: str | None = None


class ArticleDetail(BaseModel):
    """Represents a full, parsed article page with metadata and body text."""

    title: str
    url: str
    author: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    section: str | None = None
    tags: list[str] = Field(default_factory=list)
    body_text: str = ""
    summary: str | None = None
    thumbnail_url: str | None = None
    related_articles: list[HeadlineArticle] = Field(default_factory=list)


class TopicPageData(BaseModel):
    """Represents a topic/listing page and its extracted article cards."""

    url: str
    section_name: str | None = None
    description: str | None = None
    scraped_at: str = ""
    articles: list[HeadlineArticle] = Field(default_factory=list)


class HomepageData(BaseModel):
    """Aggregate container for all homepage data extracted in a scrape."""

    scraped_at: str = ""
    headlines: list[HeadlineArticle] = Field(default_factory=list)
    market_indices: list[MarketIndex] = Field(default_factory=list)
    top_stocks: list[StockQuote] = Field(default_factory=list)
    top_gainers: list[TopGainerLoser] = Field(default_factory=list)
    top_losers: list[TopGainerLoser] = Field(default_factory=list)
    crypto_prices: list[CryptoPrice] = Field(default_factory=list)
    mutual_funds: list[MutualFund] = Field(default_factory=list)
    news_sections: list[NewsSection] = Field(default_factory=list)
    opinion_articles: list[OpinionArticle] = Field(default_factory=list)
    videos: list[VideoItem] = Field(default_factory=list)
