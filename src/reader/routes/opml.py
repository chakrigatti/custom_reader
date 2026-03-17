from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from reader.database import get_db
from reader.models.schemas import OPMLImportResult

router = APIRouter(prefix="/opml", tags=["OPML"])


@router.post("/import", response_model=OPMLImportResult)
async def import_opml(file: UploadFile, db: AsyncSession = Depends(get_db)):
    from reader.services.opml import import_opml

    content = await file.read()
    xml = content.decode("utf-8")
    return await import_opml(db, xml)


@router.get("/export")
async def export_opml(db: AsyncSession = Depends(get_db)):
    from reader.services.opml import export_opml

    xml = await export_opml(db)
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="feeds.opml"'},
    )
