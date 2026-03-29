Quickstart
==========

Client usage
------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           homepage = await client.scrape_homepage()
           top_urls = [item.url for item in homepage.headlines[:5] if item.url]
           articles = await client.scrape_articles(top_urls)

           print(f"Headlines: {len(homepage.headlines)}")
           print(f"Detailed articles: {len(articles)}")


   asyncio.run(main())

Topic/list usage
----------------

.. code-block:: python

   import asyncio
   from et_scrapper import ETHttpClient


   async def main() -> None:
       async with ETHttpClient() as client:
           india = await client.scrape_india_news(limit=10)
           search_topic = await client.scrape_topic_search_news("amaravati", limit=10)
           curated = await client.scrape_curated_topic_pages(limit=10)

           print(f"India articles: {len(india.articles)}")
           print(f"Search topic articles: {len(search_topic.articles)}")
           print(f"Curated topic pages: {len(curated)}")


   asyncio.run(main())

Convenience helper functions
----------------------------

.. code-block:: python

   import asyncio
   from et_scrapper import scrape_homepage, scrape_articles


   async def main() -> None:
       hp = await scrape_homepage()
       urls = [item.url for item in hp.headlines[:3] if item.url]
       arts = await scrape_articles(urls)
       print(len(hp.headlines), len(arts))


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
