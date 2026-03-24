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
