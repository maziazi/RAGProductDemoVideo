import asyncio
import re

from crawl4ai import AsyncWebCrawler

URLS = [
    "https://www.whatastory.agency/blog",
    "https://www.whatastory.agency/case-studies",
]


def slugify(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1] or "index"
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", slug)
    return slug


async def main():
    async with AsyncWebCrawler() as crawler:
        for url in URLS:
            try:
                result = await crawler.arun(url=url)
                pages = result if isinstance(result, list) else [result]
                for page in pages:
                    if not getattr(page, "success", True):
                        continue
                    slug = slugify(getattr(page, "url", url))
                    md = page.markdown.raw_markdown if hasattr(page.markdown, "raw_markdown") else str(page.markdown)
                    with open(f"data/website/{slug}.md", "w") as f:
                        f.write(md)
                    print(f"saved data/website/{slug}.md")
            except Exception as e:
                print(f"skip {url}: {e}")


asyncio.run(main())
