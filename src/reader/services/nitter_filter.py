from __future__ import annotations

import re
from collections import OrderedDict
from urllib.parse import urlparse

from feedparser.util import FeedParserDict


def extract_username_from_feed_url(feed_url: str) -> str:
    """Extract the username from a nitter RSS feed URL.

    Expected format: {instance}/{username}/rss
    """
    parsed = urlparse(feed_url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) >= 1:
        return parts[0]
    raise ValueError(f"Cannot extract username from feed URL: {feed_url}")


def filter_nitter_entries(entries: list, feed_username: str) -> list:
    """Filter out retweets and replies, keeping only original posts."""
    filtered = []
    for entry in entries:
        title = entry.get("title", "")
        # Skip retweets
        if title.startswith("RT @"):
            continue
        # Skip replies
        if title.startswith("@"):
            continue
        # Skip entries from other authors
        author = entry.get("author", "")
        if author and author.lstrip("@").lower() != feed_username.lower():
            continue
        filtered.append(entry)
    return filtered


_STATUS_ID_RE = re.compile(r"/status/(\d+)")


def consolidate_threads(entries: list, feed_username: str) -> list:
    """Consolidate multi-tweet threads into single entries."""
    # Sort by published time ascending
    sorted_entries = sorted(
        entries,
        key=lambda e: e.get("published_parsed") or (),
    )

    # Map status_id -> group key (first status_id of the thread)
    status_to_group: dict[str, str] = {}
    # Ordered dict of group_key -> list of entries
    groups: OrderedDict[str, list] = OrderedDict()

    username_pattern = re.compile(
        rf"/{re.escape(feed_username)}/status/(\d+)", re.IGNORECASE
    )

    for entry in sorted_entries:
        link = entry.get("link", "")
        m = _STATUS_ID_RE.search(link)
        status_id = m.group(1) if m else None

        # Look for back-links in HTML content
        html = ""
        if hasattr(entry, "summary_detail") and isinstance(
            getattr(entry, "summary_detail", None), dict
        ):
            html = entry.summary_detail.get("value", "")
        elif isinstance(entry.get("summary_detail"), dict):
            html = entry.get("summary_detail", {}).get("value", "")
        if not html:
            html = entry.get("summary", "")

        # Find all back-links to the feed owner's statuses
        back_links = username_pattern.findall(html)
        group_key = None
        for back_id in back_links:
            if back_id in status_to_group:
                group_key = status_to_group[back_id]
                break

        if group_key is None:
            # Start a new group
            group_key = status_id or link
            groups[group_key] = []

        groups[group_key].append(entry)
        if status_id:
            status_to_group[status_id] = group_key

    # Merge groups into single entries
    result = []
    for entries_in_group in groups.values():
        if len(entries_in_group) == 1:
            result.append(entries_in_group[0])
            continue

        first = entries_in_group[0]
        # Collect HTML from all tweets
        html_parts = []
        for e in entries_in_group:
            part = ""
            if hasattr(e, "summary_detail") and isinstance(
                getattr(e, "summary_detail", None), dict
            ):
                part = e.summary_detail.get("value", "")
            elif isinstance(e.get("summary_detail"), dict):
                part = e.get("summary_detail", {}).get("value", "")
            if not part:
                part = e.get("summary", "")
            html_parts.append(part)

        merged_html = "<hr>".join(html_parts)

        merged = FeedParserDict(
            title=first.get("title", "") + " [thread]",
            link=first.get("link", ""),
            summary_detail=FeedParserDict(value=merged_html),
            summary=merged_html,
            published_parsed=first.get("published_parsed"),
            author=first.get("author", ""),
        )
        result.append(merged)

    return result
