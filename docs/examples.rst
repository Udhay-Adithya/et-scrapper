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
