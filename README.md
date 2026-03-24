# et-scrapper

[![Documentation Status](https://readthedocs.org/projects/et-scrapper/badge/?version=latest)](https://et-scrapper.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![GitHub Repo](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Udhay-Adithya/et-scrapper)

Python package for scraping homepage and article data from [The Economic Times](https://economictimes.indiatimes.com).

`et-scrapper` is designed for programmatic ingestion workflows such as market monitoring, editorial intelligence, and downstream AI pipelines.

## Features

- Async scraping with `httpx`
- Structured outputs using Pydantic models
- Homepage aggregation across multiple ET sections
- Detailed article extraction from article URLs
- Paywalled ETPrime content is safely skipped

## Installation

### Using uv (recommended)

```bash
uv sync
```

### Install directly from GitHub

```bash
uv pip install "git+https://github.com/Udhay-Adithya/et-scrapper.git"
```

### Build package artifacts

```bash
uv build
```

## Quick Start

### Scrape homepage data

```python
import asyncio
from et_scrapper import ETHttpClient


async def main() -> None:
    async with ETHttpClient() as client:
        homepage = await client.scrape_homepage()
        print(f"Headlines: {len(homepage.headlines)}")
        print(f"Market indices: {len(homepage.market_indices)}")


asyncio.run(main())
```

### Scrape article URLs

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
        print(f"Articles parsed: {len(articles)}")


asyncio.run(main())
```

### Chain homepage headlines to article details

```python
import asyncio
from et_scrapper import ETHttpClient


async def main() -> None:
    async with ETHttpClient() as client:
        homepage = await client.scrape_homepage()
        urls = [item.url for item in homepage.headlines[:5] if item.url]
        details = await client.scrape_articles(urls)
        print(f"Seed URLs: {len(urls)}")
        print(f"Detailed articles: {len(details)}")


asyncio.run(main())
```

## What Gets Scraped

- Headline news / top stories
- Market benchmark data (Sensex, Nifty, etc.)
- Stock quotes
- Crypto prices
- Mutual fund snippets
- Categorized section stories
- Opinion stories
- Video items
- Detailed article pages

## Documentation

Project documentation is built with Sphinx and Furo.

- Source docs: `docs/`
- Build docs locally:

```bash
uv pip install -r docs/requirements.txt
uv run sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser.

## Development

Run the diagnostic script:

```bash
uv run python manual_test.py
```

## Project Structure

```text
et-scrapper/
+-- et_scrapper/
|   +-- __init__.py
|   +-- constants.py
|   +-- models.py
|   +-- scrapers/
|   |   +-- homepage.py
|   |   +-- article.py
|   +-- utils/
|       +-- http.py
+-- docs/
+-- pyproject.toml
+-- README.md
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
