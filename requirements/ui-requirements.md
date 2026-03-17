# Custom RSS Reader — Web UI Requirements

## 1. Overview & Goals

A browser-based frontend for the custom RSS reader. It consumes the same REST API as the CLI, providing a visual interface for managing feeds, browsing articles, and reading content rendered from markdown. The UI is a single-page application (SPA) served from the same FastAPI process — no separate frontend server required.

---

## 2. Architecture

```
TypeScript source (ui/src/)
      ↓  vite build
  static/ (JS bundle + assets)
      ↓  served by
Browser (SPA)
      ↓  fetch()
FastAPI server
      ↓
  Service layer (Python)
      ↓
 SQLite database
```

The TypeScript source lives in a `ui/` directory at the project root with its own `package.json`. Vite builds the production bundle into `static/`, which FastAPI serves via a `StaticFiles` mount. Since both the API and the UI are served from the same origin in production, no CORS configuration is needed. The root path (`/`) redirects to `/static/index.html`. During development, Vite's dev server proxies API requests to the running FastAPI backend.

---

## 3. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Markup | HTML5 | Semantic, browser-native |
| Styling | CSS3 | Custom properties for theming, `prefers-color-scheme` for dark mode |
| Language | TypeScript (strict mode) | Type safety, better IDE support, catches bugs at compile time |
| Build | Vite | Fast dev server with HMR, zero-config TypeScript support, optimized production builds |
| Markdown rendering | marked | Lightweight, widely used markdown-to-HTML library |
| HTML sanitization | DOMPurify | Prevents XSS when rendering user-sourced markdown as HTML |
| Package manager | npm | Standard Node.js package management |

### Build & Dev Workflow

- `npm run dev` — starts Vite dev server with proxy to the FastAPI backend (avoids CORS during development)
- `npm run build` — compiles TypeScript, bundles, and outputs to `static/` for production serving
- `npm run typecheck` — runs `tsc --noEmit` for type validation without emitting files
- The `static/` directory (Vite build output) is served by FastAPI in production; it is gitignored and rebuilt as needed

---

## 4. Layout

```
┌──────────────────────────────────────────────┐
│  Header (app title, sync button, add feed)   │
├────────────┬─────────────────────────────────┤
│  Sidebar   │  Main Content Area              │
│            │                                 │
│  Feed list │  Article list (default)         │
│            │    — or —                       │
│            │  Article detail                 │
│            │                                 │
└────────────┴─────────────────────────────────┘
```

- **Sidebar** — fixed-width, scrollable feed list. Always visible on desktop; collapsible on narrow viewports.
- **Main content area** — switches between article list view and article detail view.
- **Header** — app title, global actions (sync all, add feed).

---

## 5. Features

### F1: View All Feeds (Sidebar)

| | |
|---|---|
| **Trigger** | Page load |
| **API** | `GET /feeds` |
| **Behavior** | Populate sidebar with feed titles. Show article count if available. Highlight the currently selected feed. An "All Feeds" entry at the top selects the unified timeline. |

### F2: View Latest Articles — Unified Timeline

| | |
|---|---|
| **Trigger** | Page load, or click "All Feeds" in sidebar |
| **API** | `GET /articles?limit=20&offset=0` |
| **Behavior** | Show articles from all feeds sorted by `published_at` descending. Each row shows title, feed name, date, and read/unread state. Pagination via "Load more" button appends the next page. |

### F3: View Articles from a Specific Feed

| | |
|---|---|
| **Trigger** | Click a feed in the sidebar |
| **API** | `GET /articles?feed_id={id}&limit=20&offset=0` |
| **Behavior** | Same layout as F2 but filtered to one feed. Sidebar highlights the selected feed. |

### F4: Read Article Content

| | |
|---|---|
| **Trigger** | Click an article row |
| **API** | `GET /articles/{id}` |
| **Behavior** | Fetch the full article JSON. Render `content_markdown` to HTML using `marked.js`, sanitize with `DOMPurify`, and display in the detail view. Show article title, author, publication date, and feed name above the content. Auto-mark the article as `read` via `PATCH /articles/{id}` with `{"state": "read"}` (fire-and-forget, do not block rendering). |

### F5: Open Original Link

| | |
|---|---|
| **Trigger** | Click "Open original" button in article detail |
| **API** | None (client-side only) |
| **Behavior** | `window.open(article.url, '_blank')` — opens the original article URL in a new tab. |

### F6: Add Feed

| | |
|---|---|
| **Trigger** | Click "Add Feed" button in header → fill URL in form → submit |
| **API** | `POST /feeds` with `{"url": "<user input>"}` |
| **Behavior** | Show an inline form or modal with a single URL input. On success (201), refresh the sidebar feed list and show a toast. On error (422, 409), show the error detail from the response body. |

### F7: Delete Feed

| | |
|---|---|
| **Trigger** | Click delete button next to a feed in the sidebar |
| **API** | `DELETE /feeds/{id}` |
| **Behavior** | Confirm via browser `confirm()` dialog. On success (204), remove the feed from the sidebar and switch to the unified timeline. Hide the delete button for the bookmark sentinel feed (`id == 1`). |

### F8: Sync Feeds

| | |
|---|---|
| **Trigger** | Click "Sync" button in header |
| **API** | `POST /sync` |
| **Behavior** | Disable the sync button and show a spinner/indicator. On success, refresh the current article list. Show a toast with the sync result. |

### F9: Mark Article State

| | |
|---|---|
| **Trigger** | Click state toggle button on an article row or in article detail |
| **API** | `PATCH /articles/{id}` with `{"state": "<new_state>"}` |
| **Behavior** | Cycle through `unread` → `read` → `read_again` → `unread`. Update the UI optimistically. Show a toast on failure and revert. |

---

## 6. UI Components

### Header
- App title ("Reader") — click returns to unified timeline
- "Sync" button — triggers F8
- "Add Feed" button — triggers F6

### Sidebar
- "All Feeds" entry (always first, bold when active)
- Feed entries: title, delete button (hidden for `id == 1`)
- Visual indicator for selected feed

### Article List
- Rows: title, feed name, relative date (`3h ago`), unread indicator (bold or dot)
- "Load more" button at the bottom when more pages exist
- Empty state message when no articles match the current filter

### Article Detail
- Back button (returns to article list, preserves scroll position)
- Article metadata: title, author, feed name, publication date
- "Open original" link/button
- State toggle button
- Rendered markdown content area

### Add Feed Form
- Single text input for URL
- Submit and cancel buttons
- Inline validation feedback

### Toast Notifications
- Auto-dismiss after 4 seconds
- Stacked in bottom-right corner
- Variants: success (green), error (red), info (neutral)

---

## 7. Navigation Flow

```
Page Load
    │
    ▼
[All Feeds timeline]  ◄──── click "All Feeds" / click header title
    │
    ├── click feed ──►  [Feed articles]
    │                        │
    │                        ├── click article ──►  [Article detail]
    │                        │                          │
    │                        │◄── click back ───────────┘
    │                        │
    ├── click article ──►  [Article detail]
    │                          │
    │◄── click back ───────────┘
    │
    ├── click "Add Feed" ──►  [Add feed form / modal]
    │◄── submit / cancel ──────┘
    │
    └── click "Sync" ──►  (refresh current view)
```

Navigation is client-side only (hash-based routing or history API). The browser back button should work naturally.

---

## 8. File Structure

### Source (`ui/`)

```
ui/
├── package.json          # Dependencies, scripts
├── tsconfig.json         # TypeScript config (strict: true)
├── vite.config.ts        # Vite config with API proxy
├── index.html            # Shell HTML entry point (Vite root)
├── src/
│   ├── main.ts           # Entry point — initializes router and mounts app
│   ├── router.ts         # Client-side router (hash-based)
│   ├── types/
│   │   ├── feed.ts       # Feed interface
│   │   ├── article.ts    # Article interface, ArticleState enum
│   │   └── api.ts        # ApiError, ProblemDetail, PaginatedResponse types
│   ├── services/
│   │   ├── api-client.ts # Shared fetch wrapper, error handling, type-safe methods
│   │   ├── feed-service.ts   # Feed CRUD operations (getAll, create, delete)
│   │   ├── article-service.ts # Article operations (list, getById, updateState)
│   │   └── sync-service.ts   # Sync trigger
│   ├── components/
│   │   ├── header.ts     # Header component (title, sync button, add feed button)
│   │   ├── sidebar.ts    # Sidebar feed list component
│   │   ├── article-list.ts   # Article list with pagination
│   │   ├── article-detail.ts # Article detail with markdown rendering
│   │   ├── add-feed-form.ts  # Add feed modal/form
│   │   └── toast.ts      # Toast notification system
│   ├── utils/
│   │   ├── date.ts       # Relative date formatting
│   │   └── markdown.ts   # marked + DOMPurify rendering pipeline
│   └── styles/
│       └── style.css     # All styles, dark mode via prefers-color-scheme
└── static/               # Build output (gitignored, served by FastAPI)
```

### Design Principles

- **Separation of concerns** — Types, API services, UI components, and utilities are in distinct layers. Components never call `fetch()` directly; they go through service functions.
- **Single responsibility** — Each module has one job. `api-client.ts` handles HTTP mechanics; `feed-service.ts` provides typed feed operations; `sidebar.ts` renders the feed list.
- **Type safety** — All API request/response shapes are defined as TypeScript interfaces. Service functions accept and return typed objects, not raw JSON.
- **Dependency direction** — `components/ → services/ → api-client.ts → types/`. No circular imports. Components depend on services; services depend on the API client; all depend on shared types.
- **Encapsulation** — Each component exports a render/mount function and manages its own DOM and event listeners internally. Components communicate via callback props or a simple event bus, not by reaching into each other's DOM.

---

## 9. Error Handling

### Shared API Client (`api-client.ts`)

All API calls go through a typed `ApiClient` class that:

1. Exposes typed methods: `get<T>(path, params?)`, `post<T>(path, body?)`, `patch<T>(path, body?)`, `delete(path)`
2. Internally calls `fetch()` with the appropriate method, headers, and JSON body
3. On success (2xx), returns the parsed and typed JSON response
4. On error (4xx/5xx), parses the RFC 7807 `application/problem+json` response body and throws an `ApiError` class containing `title`, `detail`, and `status`
5. On network failure, throws a generic connectivity error

A singleton instance is exported for use by all service modules.

### UI Error Display

- **Form errors** (422, 409) — show `detail` text inline near the form input
- **Not found** (404) — show "not found" message in the main content area
- **Server errors** (500) — show toast with `title` from the problem response
- **Network errors** — show toast: "Cannot reach server. Is the API running?"

---

## 10. Backend Changes

Two changes are required in `src/reader/server.py`:

1. Mount the Vite build output directory:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
```

2. Add a root redirect so that visiting `/` serves the UI:

```python
from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")
```

No other backend changes are needed — the existing API endpoints provide all required data.

---

## 11. Design Decisions

| Decision | Rationale |
|----------|-----------|
| TypeScript with strict mode | Catches type errors at compile time; self-documenting interfaces for API shapes; better refactoring support |
| Vite as build tool | Near-instant HMR in dev, optimized production bundles, native TypeScript support with zero config |
| No framework (vanilla TS) | The UI is simple enough to not need React/Vue; TypeScript provides structure without framework overhead |
| Layered architecture (types → services → components) | Enforces separation of concerns; services are testable in isolation; components stay focused on rendering |
| `content_markdown` from article JSON | The `GET /articles/{id}` response already includes `content_markdown` — no need for a separate `Accept: text/markdown` call |
| Dark mode via `prefers-color-scheme` | Respects OS preference automatically; no toggle needed in v1 |
| "Load more" pagination | Simpler than infinite scroll; explicit user control; avoids scroll-position bugs |
| Hide delete for bookmark feed | The bookmark sentinel feed (`id == 1`) is undeletable per the backend (403); hiding the button prevents a confusing error |
| Auto-mark as read | Opening an article detail view fires a `PATCH` to set state to `read` — matches common reader UX expectations |
| Same-origin static mount | Eliminates CORS complexity; single process to run; `uvicorn` serves everything |
| `marked` + `DOMPurify` as npm packages | Installed via npm with type definitions; tree-shaken by Vite in the production bundle |
