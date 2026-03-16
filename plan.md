# Implementation Plan: Custom RSS Reader

## Context

The project has comprehensive specs (OpenAPI 3.1.0, CLI man pages, requirements.md) but zero implementation code. We need to build a FastAPI REST server backed by SQLite, plus a click-based CLI client. The goal is a personal tool for aggregating RSS feeds, saving bookmarks, and reading articles in the terminal.

---

## Architecture

```
CLI (click + httpx)  →  HTTP  →  FastAPI server (uvicorn)
                                       ↓
                                 Service layer
                                       ↓
                              SQLAlchemy async + aiosqlite
                                       ↓
                                    SQLite
```

## Project Structure

```
custom_reader/
├── pyproject.toml
├── requirements.md                    # existing
├── docs/                              # existing specs
├── src/reader/
│   ├── __init__.py
│   ├── config.py                      # Pydantic BaseSettings
│   ├── database.py                    # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                      # SQLAlchemy ORM models (Feed, Article)
│   │   └── schemas.py                 # Pydantic request/response schemas
│   ├── errors.py                      # RFC 7807 ProblemDetail + exception handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── feeds.py                   # Feed CRUD + source-type detection
│   │   ├── articles.py                # Article CRUD + bookmark saving
│   │   ├── sync.py                    # Feed sync (single + all)
│   │   ├── content.py                 # trafilatura + markdownify extraction
│   │   ├── discovery.py               # RSS auto-discovery (bs4 + fallback paths)
│   │   └── nitter.py                  # X handle → nitter RSS URL
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── feeds.py                   # /feeds, /feeds/{id}, /feeds/{id}/sync
│   │   ├── articles.py                # /articles, /articles/{id}
│   │   └── sync.py                    # /sync
│   ├── server.py                      # FastAPI app factory, lifespan, routers
│   └── cli.py                         # click group + all subcommands
└── tests/
    ├── conftest.py                    # DB, app, client fixtures
    ├── fixtures/                      # Canned XML/HTML files
    │   ├── rss_standard.xml
    │   ├── atom_standard.xml
    │   ├── rss_minimal.xml
    │   ├── blog_with_link.html
    │   ├── blog_no_link.html
    │   ├── article_normal.html
    │   └── article_empty.html
    ├── test_feeds_api.py
    ├── test_articles_api.py
    ├── test_sync_api.py
    ├── test_source_detection.py
    ├── test_nitter.py
    └── test_cli.py
```

---

## Phase 1: Foundation

Get an installable package with a running (empty) server.

### 1.1 `pyproject.toml`
- Build system: hatchling
- Dependencies: fastapi, uvicorn[standard], aiosqlite, sqlalchemy[asyncio], click, httpx, feedparser, trafilatura, markdownify, beautifulsoup4, rich, pydantic, pydantic-settings
- Test extras: pytest, pytest-asyncio, pytest-httpx, respx
- Entry point: `reader = "reader.cli:cli"`
- Hatch packages: `["src/reader"]`

### 1.2 `config.py`
- Pydantic `BaseSettings` with `env_prefix = "READER_"`
- Fields: `database_url` (default `sqlite+aiosqlite:///reader.db`), `server_url` (default `http://localhost:8000`), `nitter_instance` (configurable)

### 1.3 `database.py`
- `create_async_engine(settings.database_url)`
- `async_sessionmaker` for session factory
- `get_db()` async dependency yielding `AsyncSession`
- `init_db()` — create all tables, insert sentinel feed (INSERT OR IGNORE)
- Enable `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL` via event listeners

### 1.4 `models/db.py` — SQLAlchemy ORM Models

```python
class Feed(Base):
    __tablename__ = "feeds"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    feed_url: Mapped[str] = mapped_column(unique=True)
    site_url: Mapped[str]
    source_type: Mapped[str]  # rss, blog, nitter, bookmark
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    last_fetched_at: Mapped[datetime | None]
    articles: Mapped[list["Article"]] = relationship(back_populates="feed", cascade="all, delete-orphan")

class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[str] = mapped_column(unique=True)
    author: Mapped[str | None]
    content_html: Mapped[str] = mapped_column(default="")
    content_markdown: Mapped[str] = mapped_column(default="")
    summary: Mapped[str | None]
    published_at: Mapped[datetime | None]
    fetched_at: Mapped[datetime] = mapped_column(default=func.now())
    state: Mapped[str] = mapped_column(default="unread")  # unread, read, read_again
    warning: Mapped[str | None]
    feed: Mapped["Feed"] = relationship(back_populates="articles")
```

### 1.5 `models/schemas.py` — Pydantic Schemas
- `FeedCreate(url: HttpUrl)`
- `FeedResponse(id, title, feed_url, site_url, source_type, created_at, last_fetched_at)` with `model_config = ConfigDict(from_attributes=True)`
- `FeedList(data: list[FeedResponse], total: int, limit: int, offset: int)`
- `ArticleCreate(url: HttpUrl)`
- `ArticleUpdate(state: Literal["unread", "read", "read_again"])`
- `ArticleResponse(...)` with `model_config = ConfigDict(from_attributes=True)`, warning excluded when None
- `ArticleList(data: list[ArticleResponse], total: int, limit: int, offset: int)`
- `FetchResult(fetched: int, feed_id: int, title: str)`
- `SyncResultList(data: list[FetchResult], total: int)`
- `ProblemDetail(type: str, title: str | None, status: int, detail: str)` with `extra="allow"` for extension fields

### 1.6 `errors.py`
- `APIError(Exception)` with `status`, `detail`, `title`, `type_uri`, `extras` dict
- Helper factories: `not_found()`, `conflict()`, `forbidden()`, `unprocessable()`, `bad_gateway()`
- FastAPI exception handler returning `JSONResponse` with `media_type="application/problem+json"`
- Override `RequestValidationError` handler for consistent 422 format

### 1.7 `server.py`
- FastAPI app with `lifespan` context manager: call `init_db()` on startup
- Register exception handlers
- Include feed, article, and sync routers
- Entry point: `uvicorn reader.server:app`

### 1.8 Test Foundation: `tests/conftest.py`
- `db` fixture: in-memory SQLite (`sqlite+aiosqlite://`), create tables, insert sentinel
- `app` fixture: override `get_db` dependency with test session
- `client` fixture: `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))`
- Fixture file loader helper
- `pytest.ini_options`: `asyncio_mode = "auto"`

---

## Phase 2: Feed CRUD

### 2.1 `services/feeds.py`
- `create_feed(db, url, config)` — calls discovery (Phase 3), checks duplicate feed_url (409), inserts, returns Feed
- `list_feeds(db, limit, offset)` — paginated query with COUNT
- `get_feed(db, feed_id)` — by ID, raise 404 if missing
- `delete_feed(db, feed_id)` — check sentinel (403), check exists (404), delete (cascade)

### 2.2 `routes/feeds.py`
- `POST /feeds` → 201 + Location header
- `GET /feeds` → query params: limit (1-200, default 50), offset (>=0, default 0)
- `GET /feeds/{id}` → 404 if missing
- `DELETE /feeds/{id}` → 204 on success, 403 for sentinel, 404 if missing

### 2.3 `tests/test_feeds_api.py`
Key cases:
- Create feed → 201
- Duplicate feed_url → 409 with existing_id
- List feeds with pagination
- Get feed by ID / 404
- Delete feed → 204 with cascade
- Delete sentinel → 403

---

## Phase 3: Source Detection & Discovery

### 3.1 `services/nitter.py`
- `is_nitter_or_handle(url)` — detect @handle or nitter domain
- `to_nitter_rss(url, nitter_instance)` — extract username, return RSS URL

### 3.2 `services/discovery.py`
- `detect_source_type(url)` → `(source_type, resolved_feed_url)`
- Logic order: nitter check → try feedparser → bs4 `<link rel="alternate">` → fallback paths (`/feed`, `/rss`, `/atom.xml`, `/feed.xml`, `/index.xml`) → 422

### 3.3 Integrate into `services/feeds.py:create_feed`

### 3.4 Tests
- `test_source_detection.py` — RSS URL, blog with link tag, blog with fallback, @handle, nitter URL, unresolvable URL
- `test_nitter.py` — handle formats, URL extraction

---

## Phase 4: Sync & Content Extraction

### 4.1 `services/content.py`
- `extract_content(html)` → `(content_html, content_markdown, metadata)`
- Uses trafilatura for extraction, markdownify for conversion
- Returns empty strings + warning if extraction fails
- `generate_summary(text, max_len=300)` — truncated plain text

### 4.2 `services/sync.py`
- `sync_feed(db, feed_id)` — get feed, verify not bookmark (422), fetch XML, parse with feedparser, deduplicate by URL (skip existing), store new articles, update last_fetched_at, return FetchResult
- `sync_all(db)` — iterate non-bookmark feeds, catch per-feed errors, return SyncResultList

### 4.3 Routes
- `POST /feeds/{id}/sync` in `routes/feeds.py`
- `POST /sync` in `routes/sync.py`

### 4.4 `tests/test_sync_api.py`
Key cases:
- Sync feed → new articles created
- Sync again → duplicates skipped
- Sync bookmark feed → 422
- Sync nonexistent feed → 404
- Sync all → skips bookmark feed, captures per-feed errors
- Upstream HTTP error → 502

### 4.5 Test fixtures
- `fixtures/rss_standard.xml` — RSS 2.0 with 3 items
- `fixtures/atom_standard.xml` — Atom with 3 entries
- `fixtures/rss_minimal.xml` — items missing optional fields

---

## Phase 5: Articles

### 5.1 `services/articles.py`
- `save_bookmark(db, url)` — validate http/https (422), check duplicate (409 + existing_id), fetch with httpx (15s timeout), extract content, store under sentinel feed (id=1), return Article with optional warning
- `list_articles(db, feed_id, state, source, limit, offset)` — validate source+feed_id mutual exclusion (422), build dynamic WHERE, paginated
- `get_article(db, article_id)` — 404 if missing
- `update_article_state(db, article_id, state)` — 404 if missing, update, return

### 5.2 `routes/articles.py`
- `POST /articles` → 201 + Location
- `GET /articles` → filters: feed_id, state, source, limit, offset
- `GET /articles/{id}` → content negotiation: `Accept: text/markdown` returns plain text, `application/json` returns JSON, else 406
- `PATCH /articles/{id}` → update state

### 5.3 `tests/test_articles_api.py`
Key cases:
- Save bookmark → 201 with content
- Save bookmark, empty extraction → 201 with warning field
- Duplicate URL → 409 with existing_id
- Invalid scheme (ftp://) → 422
- source + feed_id together → 422
- source=bookmark filter works
- Pagination correctness
- Accept: text/markdown → markdown body
- Accept: application/json → JSON
- PATCH state transitions
- Invalid state → 422

### 5.4 Test fixtures
- `fixtures/article_normal.html` — extractable article
- `fixtures/article_empty.html` — trafilatura returns None

---

## Phase 6: CLI

### 6.1 `cli.py`
Click group `reader` with synchronous httpx.Client. Base URL from config.

| Command | HTTP Call | Output |
|---------|-----------|--------|
| `add <url>` | POST /feeds | Feed title + ID |
| `feeds` | GET /feeds | Rich table |
| `remove <id>` | DELETE /feeds/{id} | Confirmation |
| `fetch [id]` | POST /feeds/{id}/sync or POST /sync | Fetch counts |
| `save <url>` | POST /articles | Article title + ID |
| `articles [--feed --state --saved]` | GET /articles | Rich table |
| `read <id>` | GET /articles/{id} (Accept: text/markdown) + PATCH state→read | Rich markdown |
| `mark <id> <state>` | PATCH /articles/{id} | Confirmation |

Error handling: catch httpx errors + non-2xx, parse problem+json, print detail, exit 1.

### 6.2 `tests/test_cli.py`
- Use click's `CliRunner`
- Mock httpx with `respx` — verify correct HTTP method/path/body for each command
- Test happy path + one error case per command
- Test output formatting

---

## Testing Strategy Summary

| Layer | Tool | DB | External HTTP |
|-------|------|-----|---------------|
| API integration tests | httpx + ASGITransport | Real in-memory SQLite | pytest-httpx mocks |
| Service unit tests | Direct function calls | Real in-memory SQLite | pytest-httpx mocks |
| CLI tests | click CliRunner | N/A (mocked HTTP) | respx mocks |

- feedparser, trafilatura, markdownify, beautifulsoup4 run against **real canned fixtures** (not mocked) — this is where integration bugs live
- Target ~80% coverage on server code, lower bar for CLI
- `asyncio_mode = "auto"` in pytest config

---

## Verification

1. **Unit/integration tests:** `pytest tests/ -v --cov=reader`
2. **Manual smoke test:**
   - Start server: `uvicorn reader.server:app`
   - Add a real RSS feed: `reader add https://feeds.arstechnica.com/arstechnica/index`
   - List feeds: `reader feeds`
   - Fetch articles: `reader fetch`
   - List articles: `reader articles`
   - Read an article: `reader read 1`
   - Save a bookmark: `reader save https://example.com/some-article`
   - Mark as read: `reader mark 1 read`
3. **OpenAPI compliance:** Compare response shapes against `docs/api/openapi.yaml`

---

## Implementation Order

Phase 1 (Foundation) → Phase 2 (Feed CRUD) → Phase 3 (Discovery) → Phase 4 (Sync) → Phase 5 (Articles) → Phase 6 (CLI)

Each phase produces testable, working code. Tests are written alongside each phase.
