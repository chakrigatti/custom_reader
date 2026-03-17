from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reader.errors import conflict, not_found
from reader.models.db import Category, Feed
from reader.models.schemas import CategoryList, CategoryResponse, FeedResponse


async def create_category(db: AsyncSession, name: str) -> CategoryResponse:
    existing = await db.execute(select(Category).where(Category.name == name))
    if existing.scalar_one_or_none():
        raise conflict(f"Category '{name}' already exists")

    category = Category(name=name)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)


async def list_categories(db: AsyncSession) -> CategoryList:
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return CategoryList(
        data=[CategoryResponse.model_validate(c) for c in categories],
        total=len(categories),
    )


async def delete_category(db: AsyncSession, category_id: int) -> None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise not_found(f"Category {category_id} not found")
    await db.delete(category)
    await db.commit()


async def rename_category(
    db: AsyncSession, category_id: int, name: str
) -> CategoryResponse:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise not_found(f"Category {category_id} not found")

    existing = await db.execute(
        select(Category).where(Category.name == name, Category.id != category_id)
    )
    if existing.scalar_one_or_none():
        raise conflict(f"Category '{name}' already exists")

    category.name = name
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)


async def set_feed_categories(
    db: AsyncSession, feed_id: int, category_ids: list[int]
) -> FeedResponse:
    result = await db.execute(
        select(Feed)
        .where(Feed.id == feed_id)
        .options(selectinload(Feed.categories))
    )
    feed = result.scalar_one_or_none()
    if not feed:
        raise not_found(f"Feed {feed_id} not found")

    if category_ids:
        cat_result = await db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        categories = cat_result.scalars().all()
        if len(categories) != len(category_ids):
            found = {c.id for c in categories}
            missing = [cid for cid in category_ids if cid not in found]
            raise not_found(f"Categories not found: {missing}")
        feed.categories = list(categories)
    else:
        feed.categories = []

    await db.commit()
    await db.refresh(feed)
    # Re-load with categories
    result = await db.execute(
        select(Feed)
        .where(Feed.id == feed_id)
        .options(selectinload(Feed.categories))
    )
    feed = result.scalar_one_or_none()
    return FeedResponse.model_validate(feed)


async def get_or_create_category(db: AsyncSession, name: str) -> Category:
    result = await db.execute(select(Category).where(Category.name == name))
    category = result.scalar_one_or_none()
    if category:
        return category
    category = Category(name=name)
    db.add(category)
    await db.flush()
    return category
