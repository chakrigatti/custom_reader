# Manhwa Tracker — Research & Approach

## Problem Statement

Track manhwa reading progress across multiple scan sites (Asura Scans, Reaper Scans, Flame Scans, Luminous Scans, etc.) and get notified when new chapters are released. These sites use bot protection (Cloudflare, CAPTCHAs) that blocks automated scraping.

---

## 1. Public APIs for Manhwa Tracking

### MangaUpdates API (Best for release tracking)
- **URL**: `https://api.mangaupdates.com/v1`
- **Auth**: Bearer token for protected endpoints; most functions publicly accessible
- **Manhwa Coverage**: Excellent — the most comprehensive database for manga/manhwa/manhua releases. Tracks releases across scan groups including Asura, Reaper, Flame, etc.
- **Features**: Manga lists, ratings, releases, notifications, messaging
- **Docs**: OpenAPI spec downloadable from the API root

### MangaDex API (Best overall API + RSS)
- **URL**: `https://api.mangadex.org` (REST v5)
- **Auth**: OAuth 2.0
- **Manhwa Coverage**: Excellent — one of the largest aggregators with strong manhwa coverage
- **Features**:
  - Full status tracking (reading, on_hold, plan_to_read, dropped, re_reading, completed)
  - `/user/follows/manga/feed` endpoint — lists new chapters for all followed manga (best built-in notification mechanism)
  - RSS feed support for follows page
  - Third-party RSS generator: [mdrss.tijlvdb.me](https://mdrss.tijlvdb.me/)
- **Docs**: [api.mangadex.org/docs](https://api.mangadex.org/docs/), [Swagger](https://api.mangadex.org/docs/swagger.html)

### AniList API (Best for progress tracking)
- **URL**: `https://graphql.anilist.co` (GraphQL)
- **Auth**: OAuth2 for write operations; reads are public
- **Manhwa Coverage**: Moderate — primarily anime/manga focused, incomplete for webtoons/manhwa
- **Features**: Full reading status support (reading, completed, paused, dropped, planning, repeating) with chapter progress
- **Docs**: [docs.anilist.co](https://docs.anilist.co/)

### MyAnimeList API
- **URL**: `https://api.myanimelist.net/v2`
- **Auth**: OAuth 2.0; requires `X-MAL-Client-ID` header
- **Manhwa Coverage**: Poor to moderate — heavily anime/manga focused
- **Alternative**: [Jikan](https://jikan.moe/) is an unofficial REST wrapper around MAL data
- **Docs**: [myanimelist.net/apiconfig/references/api/v2](https://myanimelist.net/apiconfig/references/api/v2)

### Kitsu API
- **URL**: `https://kitsu.io/api/edge` (JSON:API spec)
- **Auth**: OAuth 2.0; most GET endpoints are public
- **Manhwa Coverage**: Moderate — explicitly supports manhwa type but smaller database
- **Docs**: [kitsu.docs.apiary.io](https://kitsu.docs.apiary.io/)

### API Ranking for Manhwa Support
1. **MangaUpdates** — most comprehensive release database
2. **MangaDex** — best API with built-in follow/feed and RSS
3. **Kitsu** — explicit manhwa type support, moderate database
4. **AniList** — good API, incomplete manhwa coverage
5. **MyAnimeList** — weakest manhwa coverage

---

## 2. Existing Open-Source Tools

### Self-Hosted Trackers
- **[Mantium](https://github.com/diogovalentte/mantium)** — Self-hosted cross-site tracker. Supports MangaDex, Manga Plus, ComicK, MangaUpdates, MangaHub, and more. Can track "custom manga" for unsupported sources. Periodic chapter checking with notifications.

### Mobile Readers with Tracking
- **[Mihon](https://github.com/mihonapp/mihon)** (successor to Tachiyomi) — Open-source Android manga reader with tracker integration (MAL, AniList, Kitsu, MangaUpdates, Shikimori, Bangumi). Uses community extension repos like [Keiyoushi](https://github.com/keiyoushi/extensions) that include Asura Scans, Reaper Scans, Flame Scans sources.
- **[Kotatsu](https://github.com/KotatsuApp/Kotatsu)** — Android reader with new chapter notifications and tracking service integration.

### Discord Bots
- **[mangaupdates-bot](https://github.com/jckli/mangaupdates-bot)** — Discord bot for chapter update notifications from MangaUpdates.
- **[Discans](https://github.com/igorquintaes/Discans)** — Discord bot for manga release notifications.

### Browser Extensions
- **[manhwa-update-tracker](https://github.com/IsraelSGarcia/manhwa-update-tracker)** — Browser extension that automates chapter tracking across multiple manhwa sites and notifies of new releases.

### Scraping Tools
- **[webscraper-Asurascans-Reaperscans](https://github.com/SirMrManuel0/webscraper-Asurascans-Reaperscans)** — Python scraper specifically for Asura and Reaper Scans.
- **[magna](https://github.com/tbdsux/magna)** — Serverless scraper API supporting AsuraScans, ReaperScans, Flame-Scans.

---

## 3. Scan Site RSS/API Availability

| Site | Official API | RSS Feed | Notes |
|------|-------------|----------|-------|
| MangaDex | Yes (v5) | Yes | Best supported; has RSS generator |
| ComicK | Partial | — | Tracked by Mantium and various tools |
| Asura Scans | No | No | Community scrapers exist; site rewrites frequently break them |
| Reaper Scans | No | No | Community scrapers available |
| Flame Scans | No | No | Covered by Mihon/Keiyoushi extensions |
| Luminous Scans | No | No | Limited tooling |

**Workaround**: MangaUpdates indexes releases from all these scan groups, so polling its API is an indirect way to get chapter updates without scraping each site.

---

## 4. Browser Automation for Protected Sites

If direct site scraping is needed despite bot protections, the legitimate approach is using a **persistent browser profile** where the user has already authenticated.

### Playwright (Recommended)
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Use a dedicated profile dir — log in manually once
    context = p.chromium.launch_persistent_context(
        user_data_dir="/path/to/dedicated-chrome-profile",
        headless=False,  # headless gets blocked more aggressively
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://asuracomic.net/series/...")
    # Cloudflare clearance cookies persist in the profile
```

### Puppeteer (Alternative)
```javascript
// Attach to an already-running Chrome instance
const browser = await puppeteer.connect({
    browserWSEndpoint: 'ws://localhost:9222/devtools/browser/...'
});
// Start Chrome with: google-chrome --remote-debugging-port=9222
```

### Key Guidelines
- Use `headless=False` — headless browsers get flagged aggressively by Cloudflare
- Create a **separate** Chrome profile (not your daily driver)
- Log in and solve CAPTCHAs manually **once** — clearance cookies persist in the profile
- Use `playwright-extra` + stealth plugin to reduce fingerprinting detection
- Avoid excessive request rates — add reasonable delays between requests
- This approach does NOT bypass protections; it reuses legitimate sessions

### Stealth Plugins
- **playwright-extra** with **puppeteer-extra-plugin-stealth** patches bot-detection signals (hides `navigator.webdriver`, modifies fingerprints)
- Persistent sessions reduce Cloudflare challenge frequency since `cf_clearance` cookies are maintained

---

## 5. Recommended Architecture

Build a tracker that avoids bot-protection issues entirely by using official APIs:

1. **MangaUpdates API** — poll for new chapter releases across all scan groups
2. **MangaDex API** or **AniList API** — track reading progress
3. **Local storage** (SQLite or JSON) — store personal reading state and preferences
4. **Notifications** — Discord webhook, email, or push notifications when new chapters drop
5. **Playwright fallback** — persistent browser profile for sites not indexed by aggregators

This approach is more reliable than scraping (no breaking when sites redesign) and respects site ToS.
