from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    feed_url: Mapped[str] = mapped_column(String, unique=True)
    site_url: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    articles: Mapped[List[Article]] = relationship(
        back_populates="feed", cascade="all, delete-orphan"
    )


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("feeds.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String, unique=True)
    author: Mapped[Optional[str]] = mapped_column(String, default=None)
    content_html: Mapped[str] = mapped_column(Text, default="")
    content_markdown: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, default=None)
    published_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())
    state: Mapped[str] = mapped_column(String, default="unread")
    warning: Mapped[Optional[str]] = mapped_column(String, default=None)

    feed: Mapped[Feed] = relationship(back_populates="articles")
