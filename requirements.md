# RSS Feed Reader — Feature Document

## Overview

A personal feed reader that aggregates blog posts from various sources and provides a unified reading experience. Available as both a CLI tool and a web application, sharing the same local database.

---

## Goals

- Subscribe to blogs, RSS/Atom feeds, and X (Twitter) accounts from one place
- Get notified of new posts across all subscriptions
- Read full articles within the app (no need to open a browser)
- Track reading progress with flexible article states

---

## Sources

| Source Type | How It Works |
|-------------|-------------|
| RSS/Atom feeds | Subscribe directly by feed URL |
| Blog URLs | Auto-discover RSS feed from the blog's HTML page |
| X (Twitter) | Use nitter instances to get RSS feeds for X accounts |

**Newsletters** — dropped for now, may revisit later.

### RSS Auto-Discovery
When given a plain blog URL (not a feed URL):
1. Fetch the page and look for `<link rel="alternate">` tags pointing to RSS/Atom
2. Try common feed paths (`/feed`, `/rss`, `/atom.xml`, `/feed.xml`, `/index.xml`)
3. Subscribe to the first valid feed found

### Nitter for X/Twitter
- Convert an X handle to a nitter RSS URL
- Maintain a configurable list of nitter instances (they go down often)
- Automatically fall back to the next available instance

---

## Interfaces

### CLI
- Command-based interface (e.g., `feedreader add <url>`, `feedreader posts`)
- Full articles rendered as markdown in the terminal using the `rich` library
- All feed management, fetching, reading, and article state changes via commands

### Web UI
- Built with FastAPI + Jinja2 templates
- Feed management (add/remove subscriptions)
- Article list with filtering by feed, state, and date
- Clean reader-mode view for full articles
- Reminder queue page

**Both interfaces share the same SQLite database**, so you can switch between them freely.

---

## Article States

Each article has one of these states:

| State | Meaning |
|-------|---------|
| **Unread** | New article, not yet read (default) |
| **Read** | Article has been read |
| **Read Again** | Finished reading but want to revisit later |

---

## Timed Reminders

- Any article can be marked with a "remind later" duration (e.g., "3 days", "1 week", "12 hours")
- The app stores a future timestamp for when the article should resurface
- Reminded articles appear in a dedicated "remind" view once the time arrives
- Available in both CLI (`feedreader posts --remind`) and web UI (Remind Queue page)

---

## Feed Management

- **Add** a feed by RSS URL, blog URL, or X handle
- **List** all subscribed feeds with title, URL, and last fetch time
- **Remove** a feed (articles already fetched are retained)
- **Fetch** new posts from all feeds or a specific feed on demand

---

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | User preference |
| Database | SQLite | Simple, local, no server needed |
| CLI framework | click or typer | Clean command structure |
| Terminal rendering | rich | Markdown rendering in terminal |
| Web framework | FastAPI + Jinja2 | Lightweight, async, good DX |
| Feed parsing | feedparser | Mature RSS/Atom parser |
| HTTP client | httpx | Async support for fetching |
| Content extraction | readability-lxml or trafilatura | Extract clean article content from HTML |
| RSS discovery | beautifulsoup4 | Parse HTML to find feed links |

---

## Data Model

### Feeds
- Title, feed URL, original site URL
- Source type (rss, blog, nitter)
- Timestamps for when added and last fetched

### Articles
- Title, URL, author, full content (HTML), summary
- Publication date, fetch date
- Current state (unread / read / read_again)
- Optional remind-at timestamp for timed reminders
- Link back to parent feed

---
