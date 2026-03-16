from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.errors import APIError
from reader.models.schemas import (
    ArticleCreate,
    ArticleList,
    ArticleResponse,
    ArticleUpdate,
)

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("", status_code=201, response_model=ArticleResponse)
async def create_article(
    body: ArticleCreate, db: AsyncSession = Depends(get_db)
):
    from reader.services.articles import save_bookmark

    article = await save_bookmark(db, str(body.url))
    return JSONResponse(
        status_code=201,
        content=article.model_dump(mode="json"),
        headers={"Location": f"/articles/{article.id}"},
    )


@router.get("")
async def list_articles(
    feed_id: Optional[int] = Query(default=None),
    state: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ArticleList:
    from reader.services.articles import list_articles

    return await list_articles(db, feed_id, state, source, limit, offset)


@router.get("/{article_id}")
async def get_article(
    article_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    from reader.services.articles import get_article

    article = await get_article(db, article_id)
    accept = request.headers.get("accept", "application/json")

    if "text/markdown" in accept:
        return Response(
            content=article.content_markdown,
            media_type="text/markdown",
        )
    if "application/json" in accept or "*/*" in accept:
        return ArticleResponse.model_validate(article)

    raise APIError(406, "Not Acceptable", title="Not Acceptable")


@router.patch("/{article_id}")
async def update_article(
    article_id: int,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    from reader.services.articles import update_article_state

    return await update_article_state(db, article_id, body.state)
