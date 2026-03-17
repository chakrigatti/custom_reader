from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class FeedCreate(BaseModel):
    url: HttpUrl


class CategoryCreate(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class CategoryList(BaseModel):
    data: List[CategoryResponse]
    total: int


class FeedCategoryUpdate(BaseModel):
    category_ids: List[int]


class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TagList(BaseModel):
    data: List[TagResponse]
    total: int


class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    feed_url: str
    site_url: str
    source_type: str
    favicon_url: Optional[str] = None
    created_at: datetime
    last_fetched_at: Optional[datetime] = None
    categories: List[CategoryResponse] = []


class FeedList(BaseModel):
    data: List[FeedResponse]
    total: int
    limit: int
    offset: int


class ArticleCreate(BaseModel):
    url: HttpUrl


class ArticleUpdate(BaseModel):
    state: Literal["unread", "read", "read_again"]


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feed_id: int
    title: str
    url: str
    author: Optional[str] = None
    content_html: str
    content_markdown: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
    state: str
    warning: Optional[str] = None
    tags: List[TagResponse] = []


class ArticleList(BaseModel):
    data: List[ArticleResponse]
    total: int
    limit: int
    offset: int


class FetchResult(BaseModel):
    fetched: int
    feed_id: int
    title: str


class SyncResultList(BaseModel):
    data: List[FetchResult]
    total: int


class OPMLImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str]


class ProblemDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "about:blank"
    title: Optional[str] = None
    status: int
    detail: str
