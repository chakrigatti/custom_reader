from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.models.schemas import SyncResultList

router = APIRouter(tags=["Sync"])


@router.post("/sync")
async def sync_all(db: AsyncSession = Depends(get_db)) -> SyncResultList:
    from reader.services.sync import sync_all

    return await sync_all(db)
