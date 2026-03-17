from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reader.errors import conflict, not_found
from reader.models.db import Article, Tag
from reader.models.schemas import ArticleResponse, TagList, TagResponse


async def create_tag(db: AsyncSession, name: str) -> TagResponse:
    existing = await db.execute(select(Tag).where(Tag.name == name))
    if existing.scalar_one_or_none():
        raise conflict(f"Tag '{name}' already exists")

    tag = Tag(name=name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return TagResponse.model_validate(tag)


async def list_tags(db: AsyncSession, q: Optional[str] = None) -> TagList:
    query = select(Tag).order_by(Tag.name)
    if q:
        query = query.where(Tag.name.ilike(f"%{q}%"))
    result = await db.execute(query)
    tags = result.scalars().all()
    return TagList(
        data=[TagResponse.model_validate(t) for t in tags],
        total=len(tags),
    )


async def delete_tag(db: AsyncSession, tag_id: int) -> None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise not_found(f"Tag {tag_id} not found")
    await db.delete(tag)
    await db.commit()


async def add_tag_to_article(
    db: AsyncSession, article_id: int, tag_name: str
) -> ArticleResponse:
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one_or_none()
    if not article:
        raise not_found(f"Article {article_id} not found")

    # Get or create tag
    tag_result = await db.execute(select(Tag).where(Tag.name == tag_name))
    tag = tag_result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.flush()

    if tag not in article.tags:
        article.tags.append(tag)

    await db.commit()
    # Re-load
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one_or_none()
    return ArticleResponse.model_validate(article)


async def remove_tag_from_article(
    db: AsyncSession, article_id: int, tag_id: int
) -> ArticleResponse:
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one_or_none()
    if not article:
        raise not_found(f"Article {article_id} not found")

    tag_result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = tag_result.scalar_one_or_none()
    if not tag:
        raise not_found(f"Tag {tag_id} not found")

    if tag in article.tags:
        article.tags.remove(tag)

    await db.commit()
    # Re-load
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.tags))
    )
    article = result.scalar_one_or_none()
    return ArticleResponse.model_validate(article)
