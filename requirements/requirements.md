# Custom RSS Reader — Requirements (v1)

## 1. Overview & Goals

A personal RSS reader built for the command line. It aggregates articles from RSS/Atom feeds, blog URLs, and X/Twitter accounts (via Nitter), stores them locally in SQLite, and lets you read full articles rendered as markdown in the terminal. A FastAPI server acts as the single source of truth; the CLI is a thin HTTP client that talks to it.

---

## 2. Architecture

```
CLI (click + httpx)
        ↓ HTTP
FastAPI server
        ↓
   Service layer (Python)
        ↓
  SQLite database
```

The CLI never touches the database directly — all reads and writes go through the REST API.

---

## 3. Source Types (v1)

| Type | Input | How |
|------|-------|-----|
| RSS/Atom | Feed URL | feedparser directly |
| Blog URL | Homepage URL | beautifulsoup4 auto-discovery via `<link rel="alternate">` + common paths (`/feed`, `/rss`, `/atom.xml`, `/feed.xml`, `/index.xml`) |
| X/Twitter | Handle or nitter URL | Convert to nitter RSS URL (single configurable instance, no fallback in v1). On sync, filters out retweets and replies, keeping only original posts. Multi-tweet threads are consolidated into single articles. |
| Bookmark | Standalone URL | Fetch URL directly via httpx, extract content with trafilatura, store under sentinel feed |

---

## 4. Data Model

### feeds

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `title` | TEXT | Feed title |
| `feed_url` | TEXT UNIQUE | Resolved RSS/Atom URL |
| `site_url` | TEXT | Original site homepage |
| `source_type` | TEXT | `rss`, `blog`, `nitter`, or `bookmark` |
| `created_at` | DATETIME | When the feed was added |
| `last_fetched_at` | DATETIME | Last successful fetch time |

**Sentinel feed row:** At DB bootstrap, a reserved feed row is inserted once (idempotent) with `id = 1` (`BOOKMARK_FEED_ID`), `title = "Saved Articles"`, `feed_url = "bookmark://saved"`, `source_type = "bookmark"`. This row is undeletable and acts as the parent for all bookmark articles, preserving the `feed_id NOT NULL` FK constraint with no schema changes.

### articles

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `feed_id` | INTEGER FK | References `feeds.id` |
| `title` | TEXT | Article title |
| `url` | TEXT UNIQUE | Canonical article URL |
| `author` | TEXT | Author name (nullable) |
| `content_html` | TEXT | Raw HTML content |
| `content_markdown` | TEXT | Converted markdown (via markdownify + trafilatura) |
| `summary` | TEXT | Short excerpt or feed-provided summary |
| `published_at` | DATETIME | Publication date from feed |
| `fetched_at` | DATETIME | When the article was fetched |
| `state` | TEXT | `unread`, `read`, or `read_again` (default: `unread`) |

---

## 5. REST API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/feeds` | Add a feed (auto-detects source type from URL) |
| `GET` | `/feeds` | List all subscribed feeds |
| `DELETE` | `/feeds/{id}` | Remove a feed (returns 403 if `id == BOOKMARK_FEED_ID`) |
| `POST` | `/feeds/{id}/fetch` | Fetch new articles for one feed (skips feeds with `source_type == 'bookmark'`) |
| `POST` | `/feeds/fetch` | Fetch new articles for all feeds (skips feeds with `source_type == 'bookmark'`) |
| `POST` | `/articles` | Save a standalone URL as a bookmark article (see below) |
| `GET` | `/articles` | List articles (query params: `feed_id`, `state`, `source`) |
| `GET` | `/articles/{id}` | Get article detail (all fields) |
| `GET` | `/articles/{id}/markdown` | Get article content rendered as markdown |
| `PATCH` | `/articles/{id}` | Update article state |

### POST /articles — Save a bookmark

**Request:** `{ "url": "https://..." }`

**Processing flow:**
1. Validate URL scheme (must be `http` or `https`) → 422 if not
2. Check for duplicate URL → 409 with `{ "id": <existing_article_id> }` if already saved
3. Fetch page via `httpx.AsyncClient` (timeout=15s, follow redirects) → 422 on network/HTTP failure
4. Extract content: `trafilatura.extract(html, output_format="html")`
5. Extract metadata: `trafilatura.extract_metadata(html)` — title, author, date
6. Convert HTML to markdown via `markdownify`
7. Generate summary from first 300 chars of plain-text extraction
8. Insert article with `feed_id = BOOKMARK_FEED_ID`
9. Return full article object → 201 (if no content was extracted, store with empty content and include a `"warning"` field in the response)

### GET /articles — `source` query param

`source=bookmark` filters results to `WHERE feed_id = BOOKMARK_FEED_ID`. Omitting `source` returns all articles (no behavior change). The `source` param is mutually exclusive with `feed_id`.

---

## 6. CLI Commands

| Command | Purpose |
|---------|---------|
| `reader add <url>` | Add a feed (auto-detects type: RSS, blog, or X handle/nitter URL) |
| `reader feeds` | List all subscribed feeds |
| `reader remove <feed_id>` | Remove a feed |
| `reader fetch [feed_id]` | Fetch new articles (all feeds if no ID given) |
| `reader save <url>` | Save a standalone URL as a bookmark article (validates `http`/`https` prefix; prints `Saved article #<id>: <title>` on 201, `Already saved as article #<id>` on 409, error on 422) |
| `reader articles [--feed <id>] [--state <state>] [--saved]` | List articles with optional filters (`--saved` filters to bookmarks; mutually exclusive with `--feed`; "Feed" column shows `"Saved"` for bookmark articles) |
| `reader read <article_id>` | Render article as markdown in the terminal (via `rich`) |
| `reader mark <article_id> <state>` | Set article state (`read`, `unread`, `read_again`) |

---

## 7. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.11+ | User preference |
| API framework | FastAPI + uvicorn | Async, auto-docs, clean DX |
| Database | SQLite | Local, no server, simple |
| CLI | click + httpx | Thin HTTP client to the API |
| Feed parsing | feedparser | Mature RSS/Atom support |
| HTTP fetching | httpx | Async, used for both feed fetching and article content |
| HTML → Markdown | markdownify | Clean HTML-to-markdown conversion |
| Content extraction | trafilatura | Strips boilerplate, extracts main article content |
| RSS discovery | beautifulsoup4 | Parses `<link rel="alternate">` tags from blog HTML |
| Terminal rendering | rich | Renders markdown in the terminal |

---

## 8. V2 Backlog (deferred)

- **Timed reminders / snooze** — mark an article to resurface after N days/hours
- **Nitter instance fallback** — auto-retry list when the configured instance is down
- **Full-text search** — SQLite FTS5 across article titles and content
- **Web UI** — browser-based interface built on top of the same REST API
