# et-scrapper

A Python package to scrape news, market data, and financial information from [Economic Times](https://economictimes.indiatimes.com).

Built as an experiment for feeding ET news data into AI/LLM pipelines, with a function-first API for easy integration.

---

## Package Structure

```text
et-scrapper/
+-- et_scrapper/
|   +-- __init__.py
|   +-- constants.py        # URLs, headers, delays, parser constants
|   +-- models.py            # Pydantic data models
|   +-- scrapers/
|   |   +-- __init__.py
|   |   +-- homepage.py      # Homepage scraper (8 data types)
|   |   +-- article.py       # Article page scraper
|   +-- utils/
|       +-- __init__.py
|       +-- http.py           # ETHttpClient (function-first API)
+-- pyproject.toml
+-- README.md
```

---

## What It Scrapes

| # | Data Type | Source |
| --- | --- | --- |
| 1 | Headline News / Top Stories | Homepage |
| 2 | Market Benchmark Data | Top ticker (Sensex, Nifty, etc.) |
| 3 | Stock Quotes | Homepage stock widgets |
| 4 | Crypto Prices | Homepage crypto section |
| 5 | Mutual Fund Data | Homepage MF section |
| 6 | Categorized News Sections | Section widgets |
| 7 | Opinion / Expert Views | Opinion section |
| 8 | Videos | Video widget |
| 9 | Detailed Article Pages | Individual article URLs |

> **Note:** ETPrime (paywalled) content is automatically skipped.

---

## Setup (uv)

```bash
# 1. Install uv (if needed)
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv

# 2. Create/update project environment and install dependencies
uv sync
```

---

## Quick Start (Function-First API)

### Scrape homepage directly

```python
import asyncio
from et_scrapper import ETHttpClient


async def main() -> None:
    async with ETHttpClient() as client:
        data = await client.scrape_homepage()
        print(f"Headlines: {len(data.headlines)}")
        print(f"Market indices: {len(data.market_indices)}")


asyncio.run(main())
```

### Scrape article URLs directly

```python
import asyncio
from et_scrapper import ETHttpClient


async def main() -> None:
    urls = [
        "https://economictimes.indiatimes.com/markets/stocks/news/...",
        "https://economictimes.indiatimes.com/news/economy/...",
    ]
    async with ETHttpClient() as client:
        articles = await client.scrape_articles(urls)
        print(f"Parsed: {len(articles)}")


asyncio.run(main())
```

### Chain homepage to detailed article scrape

```python
import asyncio
from et_scrapper import ETHttpClient


async def main() -> None:
    async with ETHttpClient() as client:
        homepage = await client.scrape_homepage()
        top_urls = [item.url for item in homepage.headlines[:5] if item.url]
        articles = await client.scrape_articles(top_urls)
        print(f"Top headlines sampled: {len(top_urls)}")
        print(f"Detailed articles parsed: {len(articles)}")


asyncio.run(main())
```

---

## Publish Notes

This package now uses a publish-ready structure:

- Package code lives under `et_scrapper/`.
- `pyproject.toml` defines build backend, metadata, and dependencies.

Build commands:

```bash
uv build
```

Upload (example with Twine):

```bash
uv run python -m pip install twine
uv run twine upload dist/*
```

---

## Extended Library Example

```python
import asyncio
from et_scrapper import ETHttpClient

async def main():
    async with ETHttpClient() as client:
        homepage = await client.scrape_homepage()
        print(f"Top stories: {len(homepage.headlines)}")
        print(f"Benchmarks: {len(homepage.market_indices)}")

        article = await client.scrape_article("https://economictimes.indiatimes.com/...")
        if article:  # None if paywalled
            print(article.title)
            print(article.body_text[:500])

asyncio.run(main())
```

---

## Data Models

All models are defined in `et_scrapper/models.py` using **Pydantic v2**.

| Model | Description |
| --- | --- |
| `HeadlineArticle` | Top-story headline card from homepage sections |
| `ArticleDetail` | Full article page data (text, metadata, tags, related) |
| `MarketIndex` | Index ticker row (Sensex/Nifty etc.) |
| `StockQuote` | Stock quote widget row |
| `CryptoPrice` | Crypto widget row |
| `MutualFund` | Mutual-fund card or row |
| `SectionArticle` | Article entry inside a section block |
| `NewsSection` | Categorized section with article list |
| `OpinionArticle` | Opinion/expert item |
| `VideoItem` | Video metadata card |
| `HomepageData` | Aggregated homepage response object |

---

## Dependencies

- `httpx` — async HTTP client
- `beautifulsoup4` — HTML parsing
- `lxml` — fast HTML parser backend
- `pydantic` — data validation and serialisation

---

## Notes

- Random delays (1.5–4s) are added between requests to avoid rate limiting.
- Browser-like headers are used to reduce bot detection.
- CSS selectors may need updating if ET changes their page structure.
- This project is for personal/experimental use only.
