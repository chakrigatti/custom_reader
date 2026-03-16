from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reader.errors import conflict, forbidden, not_found
from reader.models.db import Article, Feed
from reader.models.schemas import FeedList, FeedResponse


async def create_feed(db: AsyncSession, url: str) -> FeedResponse:
    from reader.services.discovery import detect_source_type

    source_type, resolved_url, title, site_url = await detect_source_type(url)

    existing = await db.execute(
        select(Feed).where(Feed.feed_url == resolved_url)
    )
    existing_feed = existing.scalar_one_or_none()
    if existing_feed:
        raise conflict(
            f"Feed already exists with URL: {resolved_url}",
            existing_id=existing_feed.id,
        )

    feed = Feed(
        title=title,
        feed_url=resolved_url,
        site_url=site_url,
        source_type=source_type,
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)
    return FeedResponse.model_validate(feed)


async def list_feeds(
    db: AsyncSession, limit: int, offset: int
) -> FeedList:
    total_result = await db.execute(select(func.count(Feed.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Feed).order_by(Feed.id).limit(limit).offset(offset)
    )
    feeds = result.scalars().all()

    return FeedList(
        data=[FeedResponse.model_validate(f) for f in feeds],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_feed(db: AsyncSession, feed_id: int) -> FeedResponse:
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise not_found(f"Feed {feed_id} not found")
    return FeedResponse.model_validate(feed)


async def delete_feed(db: AsyncSession, feed_id: int) -> None:
    if feed_id == 1:
        raise forbidden("Cannot delete the sentinel feed")

    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise not_found(f"Feed {feed_id} not found")

    await db.delete(feed)
    await db.commit()
