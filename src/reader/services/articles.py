from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reader.errors import bad_gateway, conflict, not_found, unprocessable
from reader.models.db import Article, FeedCategory, Tag
from reader.models.schemas import ArticleList, ArticleResponse
from reader.services.content import extract_content


async def save_bookmark(db: AsyncSession, url: str) -> ArticleResponse:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise unprocessable(
            f"Invalid URL scheme: {parsed.scheme}. Only http and https are supported."
        )

    existing = await db.execute(select(Article).where(Article.url == url))
    existing_article = existing.scalar_one_or_none()
    if existing_article:
        raise conflict(
            f"Article already saved with URL: {url}",
            existing_id=existing_article.id,
        )

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        raise bad_gateway(f"Failed to fetch URL: {e}")

    title, content_html, content_markdown, summary, author, warning = extract_content(
        html, url
    )

    article = Article(
        feed_id=1,
        title=title or url,
        url=url,
        author=author,
        content_html=content_html,
        content_markdown=content_markdown,
        summary=summary,
        state="unread",
        warning=warning,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    # Re-load with tags
    result = await db.execute(
        select(Article)
        .where(Article.id == article.id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one()
    return ArticleResponse.model_validate(article)


async def list_articles(
    db: AsyncSession,
    feed_id: Optional[int],
    state: Optional[str],
    source: Optional[str],
    limit: int,
    offset: int,
    tag: Optional[str] = None,
    category_id: Optional[int] = None,
) -> ArticleList:
    if source and feed_id:
        raise unprocessable("Cannot specify both 'source' and 'feed_id'")

    query = select(Article).options(selectinload(Article.tags))
    count_query = select(func.count(Article.id))

    if feed_id is not None:
        query = query.where(Article.feed_id == feed_id)
        count_query = count_query.where(Article.feed_id == feed_id)
    if state is not None:
        query = query.where(Article.state == state)
        count_query = count_query.where(Article.state == state)
    if source == "bookmark":
        query = query.where(Article.feed_id == 1)
        count_query = count_query.where(Article.feed_id == 1)
    if tag:
        from reader.models.db import ArticleTag
        query = query.join(ArticleTag, Article.id == ArticleTag.article_id).join(
            Tag, ArticleTag.tag_id == Tag.id
        ).where(Tag.name == tag)
        count_query = count_query.join(
            ArticleTag, Article.id == ArticleTag.article_id
        ).join(Tag, ArticleTag.tag_id == Tag.id).where(Tag.name == tag)
    if category_id is not None:
        query = query.join(
            FeedCategory, Article.feed_id == FeedCategory.feed_id
        ).where(FeedCategory.category_id == category_id)
        count_query = count_query.join(
            FeedCategory, Article.feed_id == FeedCategory.feed_id
        ).where(FeedCategory.category_id == category_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(
        query.order_by(Article.id.desc()).limit(limit).offset(offset)
    )
    articles = result.scalars().unique().all()

    return ArticleList(
        data=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_article(db: AsyncSession, article_id: int) -> Article:
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one_or_none()
    if not article:
        raise not_found(f"Article {article_id} not found")
    return article


async def update_article_state(
    db: AsyncSession, article_id: int, state: str
) -> ArticleResponse:
    article = await get_article(db, article_id)
    article.state = state
    await db.commit()
    await db.refresh(article)
    # Re-load with tags
    result = await db.execute(
        select(Article)
        .where(Article.id == article.id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one()
    return ArticleResponse.model_validate(article)
