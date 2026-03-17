from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.models.schemas import (
    ArticleResponse,
    TagCreate,
    TagList,
    TagResponse,
)

router = APIRouter(tags=["Tags"])


@router.post("/tags", status_code=201, response_model=TagResponse)
async def create_tag(body: TagCreate, db: AsyncSession = Depends(get_db)):
    from reader.services.tags import create_tag

    tag = await create_tag(db, body.name)
    return JSONResponse(
        status_code=201,
        content=tag.model_dump(mode="json"),
    )


@router.get("/tags", response_model=TagList)
async def list_tags(
    q: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from reader.services.tags import list_tags

    return await list_tags(db, q)


@router.delete("/tags/{tag_id}", status_code=204)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    from reader.services.tags import delete_tag

    await delete_tag(db, tag_id)


@router.post("/articles/{article_id}/tags", response_model=ArticleResponse)
async def add_tag_to_article(
    article_id: int,
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
):
    from reader.services.tags import add_tag_to_article

    return await add_tag_to_article(db, article_id, body.name)


@router.delete(
    "/articles/{article_id}/tags/{tag_id}", response_model=ArticleResponse
)
async def remove_tag_from_article(
    article_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
):
    from reader.services.tags import remove_tag_from_article

    return await remove_tag_from_article(db, article_id, tag_id)
