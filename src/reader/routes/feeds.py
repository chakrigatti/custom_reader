from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.models.schemas import FeedCreate, FeedList, FeedResponse, FetchResult

router = APIRouter(prefix="/feeds", tags=["Feeds"])


@router.post("", status_code=201, response_model=FeedResponse)
async def create_feed(
    body: FeedCreate, db: AsyncSession = Depends(get_db)
):
    from reader.services.feeds import create_feed

    feed = await create_feed(db, str(body.url))
    return JSONResponse(
        status_code=201,
        content=feed.model_dump(mode="json"),
        headers={"Location": f"/feeds/{feed.id}"},
    )


@router.get("")
async def list_feeds(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> FeedList:
    from reader.services.feeds import list_feeds

    return await list_feeds(db, limit, offset)


@router.get("/{feed_id}")
async def get_feed(
    feed_id: int, db: AsyncSession = Depends(get_db)
) -> FeedResponse:
    from reader.services.feeds import get_feed

    return await get_feed(db, feed_id)


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(
    feed_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    from reader.services.feeds import delete_feed

    await delete_feed(db, feed_id)


@router.post("/{feed_id}/sync")
async def sync_feed(
    feed_id: int, db: AsyncSession = Depends(get_db)
) -> FetchResult:
    from reader.services.sync import sync_feed

    return await sync_feed(db, feed_id)
