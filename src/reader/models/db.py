from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FeedCategory(Base):
    __tablename__ = "feed_categories"

    feed_id: Mapped[int] = mapped_column(
        ForeignKey("feeds.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    feeds: Mapped[List[Feed]] = relationship(
        secondary="feed_categories", back_populates="categories"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    articles: Mapped[List[Article]] = relationship(
        secondary="article_tags", back_populates="tags"
    )


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    feed_url: Mapped[str] = mapped_column(String, unique=True)
    site_url: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    favicon_url: Mapped[Optional[str]] = mapped_column(String, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    articles: Mapped[List[Article]] = relationship(
        back_populates="feed", cascade="all, delete-orphan"
    )
    categories: Mapped[List[Category]] = relationship(
        secondary="feed_categories", back_populates="feeds"
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
    tags: Mapped[List[Tag]] = relationship(
        secondary="article_tags", back_populates="articles"
    )
