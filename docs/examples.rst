Usage Examples
==============

This page collects common usage patterns for the package.

Homepage scrape
---------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           homepage = await client.scrape_homepage()
           print(len(homepage.headlines))
           print(len(homepage.market_indices))


   asyncio.run(main())

Single article scrape
---------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       url = "https://economictimes.indiatimes.com/news/economy/..."
       async with ETHttpClient() as client:
           article = await client.scrape_article(url)
           if article is None:
               print("Article was not accessible (possibly paywalled).")
               return
           print(article.title)
           print(article.body_text[:200])


   asyncio.run(main())

Multiple article scrape
-----------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       urls = [
           "https://economictimes.indiatimes.com/markets/stocks/news/...",
           "https://economictimes.indiatimes.com/news/economy/...",
       ]
       async with ETHttpClient() as client:
           articles = await client.scrape_articles(urls)
           print(f"Parsed {len(articles)} articles")


   asyncio.run(main())

Homepage to article chain
-------------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           homepage = await client.scrape_homepage()
           urls = [item.url for item in homepage.headlines[:10] if item.url]
           details = await client.scrape_articles(urls)
           print(f"Input URLs: {len(urls)}")
           print(f"Detailed results: {len(details)}")


   asyncio.run(main())

Topic wrapper scrape
--------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           wrapped_topics = [
               await client.scrape_trending_news(limit=10),
               await client.scrape_india_news(limit=10),
               await client.scrape_economy_finance_news(limit=10),
               await client.scrape_politics_news(limit=10),
               await client.scrape_sports_news(limit=10),
               await client.scrape_tech_internet_news(limit=10),
               await client.scrape_stock_market_news(limit=10),
           ]

           for topic in wrapped_topics:
               print(topic.section_name, len(topic.articles))


   asyncio.run(main())

Generic topic-search route
--------------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           # Builds: /topic/amaravati/news
           topic_page = await client.scrape_topic_search_news("amaravati", limit=10)
           print(topic_page.url)
           print(len(topic_page.articles))


   asyncio.run(main())

Curated topic pages in one call
-------------------------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           topic_pages = await client.scrape_curated_topic_pages(limit=10)
           print(f"Topic pages: {len(topic_pages)}")
           if topic_pages:
               print(topic_pages[0].section_name)


   asyncio.run(main())

Helper functions
----------------

.. code-block:: python

   import asyncio
   from et_scrapper import scrape_homepage, scrape_articles


   async def main() -> None:
       homepage = await scrape_homepage()
       urls = [item.url for item in homepage.headlines[:3] if item.url]
       details = await scrape_articles(urls)
       print(len(homepage.headlines), len(details))


   asyncio.run(main())

Topic helper functions
----------------------

.. code-block:: python

   import asyncio
   from et_scrapper import scrape_topic_search_news, scrape_curated_topic_pages


   async def main() -> None:
       topic = await scrape_topic_search_news("amaravati", limit=10)
       curated = await scrape_curated_topic_pages(limit=10)

       print(topic.section_name, len(topic.articles))
       print(f"Curated pages: {len(curated)}")


   asyncio.run(main())
