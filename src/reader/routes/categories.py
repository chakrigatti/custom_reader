from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.models.schemas import (
    CategoryCreate,
    CategoryList,
    CategoryResponse,
    FeedCategoryUpdate,
    FeedResponse,
)

router = APIRouter(tags=["Categories"])


@router.post("/categories", status_code=201, response_model=CategoryResponse)
async def create_category(
    body: CategoryCreate, db: AsyncSession = Depends(get_db)
):
    from reader.services.categories import create_category

    category = await create_category(db, body.name)
    return JSONResponse(
        status_code=201,
        content=category.model_dump(mode="json"),
    )


@router.get("/categories", response_model=CategoryList)
async def list_categories(db: AsyncSession = Depends(get_db)):
    from reader.services.categories import list_categories

    return await list_categories(db)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def rename_category(
    category_id: int,
    body: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    from reader.services.categories import rename_category

    return await rename_category(db, category_id, body.name)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int, db: AsyncSession = Depends(get_db)
):
    from reader.services.categories import delete_category

    await delete_category(db, category_id)


@router.put("/feeds/{feed_id}/categories", response_model=FeedResponse)
async def set_feed_categories(
    feed_id: int,
    body: FeedCategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    from reader.services.categories import set_feed_categories

    return await set_feed_categories(db, feed_id, body.category_ids)
