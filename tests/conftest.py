from __future__ import annotations

import pathlib
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from reader.models.db import Base

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a test fixture file by name."""
    return (FIXTURES_DIR / name).read_text()


@pytest_asyncio.fixture()
async def db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "INSERT OR IGNORE INTO feeds (id, title, feed_url, site_url, source_type) "
                "VALUES (1, 'Saved Articles', 'bookmark://saved', 'bookmark://saved', 'bookmark')"
            )
        )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture()
async def app(db: AsyncSession):
    from reader.database import get_db
    from reader.server import app as _app

    async def _override_db():
        yield db

    _app.dependency_overrides[get_db] = _override_db
    yield _app
    _app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
