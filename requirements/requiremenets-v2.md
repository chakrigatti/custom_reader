# Custom RSS Reader — V2 Feature Suggestions

## Context

The v1 reader is fully implemented with a FastAPI backend, SQLite database, vanilla TypeScript SPA, and Click CLI. It supports RSS/Atom feeds, blog auto-discovery, X/Twitter via Nitter, and standalone bookmarks. The v1 requirements doc listed 4 backlog items for v2 (one — Web UI — is already done). This plan proposes a comprehensive set of v2 features based on research of popular RSS readers (Feedly, Inoreader, Miniflux, FreshRSS, NewsBlur, NetNewsWire) and open-source GitHub projects.

---

## TIER 0: V1 BACKLOG CARRYOVER (Must-do)

### 0.1 Full-Text Search (SQLite FTS5)
Create an FTS5 virtual table mirroring article titles and `content_markdown`. Keep in sync via SQLAlchemy event hooks or triggers. Expose via `GET /articles?q=search+terms`. FTS5 supports ranking, prefix queries, phrase matching, and boolean operators natively — zero new dependencies.
- **UI**: Search input in the header, results in timeline view
- **CLI**: `reader search <query>`

### 0.2 Timed Reminders / Snooze
Add `snoozed_until` (nullable datetime) to `articles`. `PATCH /articles/{id}` accepts `{"snooze": "3d"}`. A lightweight background coroutine (started in FastAPI lifespan) checks every 60s and flips snoozed articles back to `unread`. Snoozed articles hidden from normal listing.
- **UI**: Snooze button in article detail with preset durations dropdown
- **CLI**: `reader snooze <article_id> <duration>`

### 0.3 Nitter Instance Fallback
Replace single `READER_NITTER_INSTANCE` with `READER_NITTER_INSTANCES` (comma-separated list). During sync of nitter feeds, try each instance in order until one responds. Optionally track last-known-good instance.
- No UI changes needed (transparent to user)

---

## TIER 1: HIGH PRIORITY (High value, moderate effort)

### 1.1 OPML Import/Export
`POST /opml/import` accepts OPML XML file, bulk-creates feeds. `GET /opml/export` returns feed list as OPML 2.0 XML. Use `xml.etree.ElementTree` (stdlib) — no new dependency. This is the universal RSS subscription interchange format, essential for onboarding and portability.
- **UI**: Import (file upload) and export buttons in a manage feeds view
- **CLI**: `reader import <file.opml>`, `reader export [--output file.opml]`

### 1.2 Folder/Category Organization
New `categories` table and `feed_categories` junction table. Feeds can belong to multiple categories. Sidebar groups feeds by category with collapsible sections. Timeline filterable by category.
- Integrates with OPML (categories map to OPML folder nesting)
- **CLI**: `reader categories`, `reader categorize <feed_id> <category>`

### 1.3 Keyboard Shortcuts
`j`/`k` next/prev article, `o`/`Enter` open, `b` back, `m` cycle state, `r` refresh, `/` focus search, `?` help overlay. UI-only change, zero backend work. Disable when typing in input fields.

### 1.4 Article Tagging
New `tags` and `article_tags` tables. Tags are user-created on-the-fly with type-ahead. Articles filterable by tag via `GET /articles?tag=...`. Provides cross-feed organization (e.g., "ai", "to-reference", "project-x").
- **UI**: Tag chips in article detail, click-to-filter in list view
- **CLI**: `reader tag <article_id> <tag>`, `reader articles --tag <tag>`

### 1.5 Feed Health Monitoring
Add `last_error`, `consecutive_failures`, `last_succeeded_at` to `feeds` table. Update during sync. Show green/yellow/red dot in sidebar. Dedicated `GET /feeds/{id}/health` endpoint. Helps users identify and clean up broken feeds.

### 1.6 Dark Mode Manual Toggle
Three-way toggle: light / dark / auto. Store in `localStorage`. Apply via `data-theme` attribute on `<html>` with CSS custom properties. UI-only, trivial to implement.

---

## TIER 2: MEDIUM PRIORITY (Good value, moderate-to-significant effort)

### 2.1 Content Filtering Rules
Per-feed or global rules that auto-mark articles as read or auto-tag based on keyword/regex patterns in title or content. New `filter_rules` table. Applied during sync after article creation.
- **UI**: Rules management page in feed settings
- **CLI**: `reader rules add ...`, `reader rules list`

### 2.2 Reading Time Estimates
Calculate from word count of `content_markdown` (~230 wpm). Store as `reading_minutes` on `Article`. Display as "5 min read" badge. Near-zero effort for meaningful UX improvement.

### 2.3 Multiple View Layouts
List (current, compact), card (grid with thumbnails), magazine (featured + smaller cards). Store preference in `localStorage`. Extract thumbnail URL from first `<img>` during content extraction. Add `thumbnail_url` column to Article. UI-only toggle.

### 2.4 Bulk Operations
Select multiple articles for batch actions: mark read/unread, tag, delete. `PATCH /articles/bulk` accepting `{"ids": [...], "state": "read"}` or `{"feed_id": 5, "state": "read"}` for mark-all-in-feed.
- **UI**: Checkbox column, floating action bar
- **CLI**: `reader mark-all --feed <id> read`

### 2.5 Article Deduplication
During sync, normalize URLs (strip `utm_*`, `ref`, `source` params) and check for existing articles before inserting. Light-touch: just skip duplicates. Optionally add `canonical_url` column.

### 2.6 JSON Feed Format Support
Add detection in discovery service (Content-Type `application/feed+json`, URL ending in `feed.json`). New parser for the JSON Feed spec (simple JSON schema). Maps to existing Article model — no schema changes.

### 2.7 Infinite Scroll
Replace pagination with `IntersectionObserver` on a sentinel element. Append new articles to DOM using existing `limit`/`offset` API. UI-only change. Optionally add virtual scrolling for large lists.

### 2.8 Feed Favicons
Fetch and cache site favicons during feed creation (try `/favicon.ico`, parse `<link rel="icon">`). Store as data URI or URL in new `favicon_url` column on Feed. Display in sidebar. Fallback: colored circle with first letter.

---

## TIER 3: LOWER PRIORITY (Nice-to-have, higher effort or niche)

### 3.1 AI Summarization
Generate summaries via local LLM (ollama) or external API (OpenAI/Anthropic). Fully opt-in. `POST /articles/{id}/summarize`. Config: `READER_AI_PROVIDER`, `READER_AI_MODEL`, `READER_AI_API_KEY`. No AI dependency in core app.

### 3.2 Content Annotations (Highlights & Notes)
New `annotations` table with `article_id`, `text_fragment`, `note`, `created_at`. Text selection popup with highlight/note buttons. Turns reader into a research tool. Significant frontend complexity.

### 3.3 Offline Reading / PWA
Service worker + web app manifest for installability and offline access. Cache articles in IndexedDB. Sync queue for offline state changes. Moderate frontend effort.

### 3.4 Newsletter Ingestion (Email-to-Feed)
Embedded SMTP server (via `aiosmtpd`) converts incoming emails to articles. Simpler alternative: watch a Maildir folder. Stored under a "Newsletters" sentinel feed.

### 3.5 Third-Party Integrations
"Send to" action framework for Pocket, Readwise, Wallabag, etc. Each integration needs its own API client and auth. Start with one (Pocket has the simplest API).

### 3.6 Article Statistics / Analytics
Track reading habits: articles/day, most-read feeds, reading streaks. New `reading_events` table. Dashboard view with simple SVG charts. Fun but doesn't affect core functionality.

### 3.7 WebSub (PubSubHubbub) for Real-Time Updates
Subscribe to hubs for instant push updates instead of polling. Requires reader to be publicly accessible — impractical for most local deployments. Opt-in with `READER_PUBLIC_URL` config.

### 3.8 Custom CSS Per Feed
`custom_css` text column on Feed, injected as `<style>` when rendering that feed's articles. Niche but useful for feeds with broken formatting.

---

## RECOMMENDED IMPLEMENTATION ORDER

| Phase | Features | Rationale |
|-------|----------|-----------|
| **Phase 1 — Foundation** | 0.1 (FTS5), 1.6 (dark toggle), 1.3 (keyboard shortcuts), 2.2 (reading time) | Independent, high-impact, low-risk. Search is the biggest single quality-of-life win. |
| **Phase 2 — Organization** | 1.1 (OPML), 1.2 (categories), 1.4 (tagging), 2.8 (favicons) | Build on each other; transform flat list into organized system. |
| **Phase 3 — Robustness** | 0.2 (snooze), 0.3 (nitter fallback), 1.5 (feed health), 2.5 (dedup), 2.6 (JSON Feed) | Harden the system and complete v1 backlog promises. |
| **Phase 4 — Power Features** | 2.1 (filter rules), 2.4 (bulk ops), 2.7 (infinite scroll), 2.3 (view layouts) | Serve power users managing large volumes of content. |
| **Phase 5 — Advanced** | 3.1 (AI summarization), 3.2 (annotations), 3.3 (PWA), Tier 3 as desired | Pick based on interest and time. |
