# Plan: Twitter/X Post Filtering for Nitter Feeds

## Context

When syncing Twitter/X feeds (via Nitter RSS), the reader currently stores every entry without filtering. The user wants **only original posts from the handle owner** — no retweets, no replies from others. Additionally, multi-tweet threads by the same author should be consolidated into single articles for a cleaner reading experience.

Nitter's `/username/rss` endpoint already excludes replies by default, but still includes retweets. No open-source RSS tool currently consolidates threads — this will be a differentiating feature.

## Approach

Create a new `nitter_filter.py` module with all filtering/thread logic, then wire it into `sync_feed()` with a 6-line conditional. No schema changes needed.

## File Changes

### 1. New: `src/reader/services/nitter_filter.py`

Three public functions:

**`extract_username_from_feed_url(feed_url: str) -> str`**
- Parses the nitter feed URL (`{instance}/{username}/rss`) to get the owner's username

**`filter_nitter_entries(entries: list, feed_username: str) -> list`**
- Skips entries where title starts with `RT @` (retweets)
- Skips entries where title starts with `@` (replies that leaked through)
- Skips entries where `author` field doesn't match feed owner (secondary retweet check)
- All comparisons case-insensitive

**`consolidate_threads(entries: list, feed_username: str) -> list`**
- Sorts entries by `published_parsed` ascending
- For each entry, extracts status ID from link URL (`/status/\d+`)
- Checks entry HTML for back-links to a previous status from the same user (Nitter includes these in thread continuations)
- If back-link found to a known status, appends to that thread group; otherwise starts new group
- Merges each multi-tweet group into a single entry:
  - Title: first tweet's title + ` [thread]` suffix
  - Link: first tweet's URL (used as dedup key)
  - Content: all tweets joined with `<hr>` separator
  - Timestamp: first tweet's `published_parsed`
- Returns merged entry as plain dict with `summary_detail` key (compatible with `extract_from_feed_entry` which falls through `content` -> `summary_detail` -> `summary`)

### 2. Modify: `src/reader/services/sync.py` (lines 41-44)

Insert between `parsed = feedparser.parse(raw)` and the `for entry` loop:

```python
entries = parsed.entries
if feed.source_type == "nitter":
    username = extract_username_from_feed_url(feed.feed_url)
    entries = filter_nitter_entries(entries, username)
    entries = consolidate_threads(entries, username)
```

Change `for entry in parsed.entries:` to `for entry in entries:`. Add import at top of file.

### 3. New: `tests/fixtures/nitter_feed.xml`

RSS 2.0 fixture with:
- 2-3 original tweets from the feed owner
- 1-2 retweets (`RT @other:` prefix)
- A 3-tweet thread (sequential, with reply back-links in HTML)

### 4. New: `tests/test_nitter_filter.py`

Unit tests for all three public functions + integration test parsing the XML fixture through the full filter pipeline.

### 5. Modify: `tests/test_sync_api.py`

Add integration test: create nitter feed, mock HTTP with fixture XML, call `sync_feed()`, assert retweets excluded and threads consolidated.

## Known Edge Case: Partial Thread Sync

If the first tweet of a thread is already saved from a previous sync, the consolidated entry's URL (first tweet's URL) will hit the dedup check and the whole group gets skipped. Later thread tweets are also skipped since they appear as part of a consolidated group. In practice, threads usually arrive in a single sync batch. A future enhancement could update existing articles when new thread tweets appear, but this is deferred.

## Verification

1. Run existing tests: `pytest tests/` — all pass (no regressions)
2. Run new tests: `pytest tests/test_nitter_filter.py` — all pass
3. Manual test: add a Twitter handle (`reader add @someone`), sync, verify only original posts appear and threads are merged
