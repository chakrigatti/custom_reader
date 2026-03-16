from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reader.errors import bad_gateway, not_found, unprocessable
from reader.models.db import Article, Feed
from reader.models.schemas import FetchResult, SyncResultList
from reader.services.content import extract_from_feed_entry

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def sync_feed(db: AsyncSession, feed_id: int) -> FetchResult:
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise not_found(f"Feed {feed_id} not found")
    if feed.source_type == "bookmark":
        raise unprocessable("Cannot sync a bookmark feed")

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, headers=BROWSER_HEADERS
        ) as client:
            response = await client.get(feed.feed_url)
            response.raise_for_status()
            raw = response.text
    except httpx.HTTPError as e:
        raise bad_gateway(f"Failed to fetch feed: {e}")

    parsed = feedparser.parse(raw)
    fetched_count = 0

    for entry in parsed.entries:
        url = entry.get("link")
        if not url:
            continue

        existing = await db.execute(select(Article).where(Article.url == url))
        if existing.scalar_one_or_none():
            continue

        title, content_html, content_markdown, summary, author = extract_from_feed_entry(
            entry
        )

        published_at: Optional[datetime] = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(
                    *entry.published_parsed[:6], tzinfo=timezone.utc
                )
            except (TypeError, ValueError):
                pass

        article = Article(
            feed_id=feed_id,
            title=title or url,
            url=url,
            author=author,
            content_html=content_html,
            content_markdown=content_markdown,
            summary=summary,
            published_at=published_at,
            state="unread",
        )
        db.add(article)
        fetched_count += 1

    feed.last_fetched_at = datetime.now(timezone.utc)
    await db.commit()

    return FetchResult(fetched=fetched_count, feed_id=feed.id, title=feed.title)


async def sync_all(db: AsyncSession) -> SyncResultList:
    result = await db.execute(
        select(Feed).where(Feed.source_type != "bookmark")
    )
    feeds = result.scalars().all()

    results = []
    for feed in feeds:
        try:
            fetch_result = await sync_feed(db, feed.id)
            results.append(fetch_result)
        except Exception:
            results.append(
                FetchResult(fetched=0, feed_id=feed.id, title=feed.title)
            )

    return SyncResultList(data=results, total=len(results))
