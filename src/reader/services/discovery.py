from __future__ import annotations

from typing import Tuple
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup

from reader.errors import unprocessable
from reader.services.nitter import is_nitter_or_handle, to_nitter_rss

FALLBACK_PATHS = ["/feed", "/rss", "/atom.xml", "/feed.xml", "/index.xml"]

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def detect_source_type(
    url: str,
) -> Tuple[str, str, str, str]:
    """Detect the source type and resolve the feed URL.

    Returns (source_type, resolved_feed_url, title, site_url).
    """
    from reader.config import settings

    # Check for nitter/X handle first
    if is_nitter_or_handle(url):
        feed_url = to_nitter_rss(url, settings.nitter_instance)
        username = feed_url.rsplit("/", 2)[-2]
        return "nitter", feed_url, "@{}".format(username), url

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=15.0, headers=BROWSER_HEADERS
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise unprocessable("Could not reach URL: {}".format(e))

        content_type = response.headers.get("content-type", "")
        body = response.text

        # Try parsing as feed directly
        if _looks_like_feed(content_type, body):
            parsed = feedparser.parse(body)
            title = parsed.feed.get("title", url)
            site_url = parsed.feed.get("link", url)
            return "rss", str(response.url), title, site_url

        # Try discovering from HTML
        soup = BeautifulSoup(body, "html.parser")
        feed_link = soup.find(
            "link",
            rel="alternate",
            type=lambda t: t and ("rss" in t or "atom" in t),
        )
        if feed_link and feed_link.get("href"):
            discovered_url = _resolve_url(str(response.url), feed_link["href"])
            title = await _fetch_feed_title(client, discovered_url, url)
            return "blog", discovered_url, title, str(response.url)

        # Try fallback paths
        base = "{}://{}".format(response.url.scheme, response.url.host)
        for path in FALLBACK_PATHS:
            candidate = base + path
            try:
                resp = await client.get(candidate)
                if resp.status_code == 200 and _looks_like_feed(
                    resp.headers.get("content-type", ""), resp.text
                ):
                    parsed = feedparser.parse(resp.text)
                    title = parsed.feed.get("title", url)
                    return "blog", candidate, title, str(response.url)
            except httpx.HTTPError:
                continue

    raise unprocessable("Could not discover a feed at: {}".format(url))


def _looks_like_feed(content_type: str, body: str) -> bool:
    if any(t in content_type for t in ["xml", "rss", "atom"]):
        return True
    parsed = feedparser.parse(body)
    return bool(parsed.entries) and not parsed.bozo


def _resolve_url(base: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return urljoin(base, href)


async def _fetch_feed_title(
    client: httpx.AsyncClient, feed_url: str, fallback: str
) -> str:
    try:
        resp = await client.get(feed_url)
        parsed = feedparser.parse(resp.text)
        return parsed.feed.get("title", fallback)
    except Exception:
        return fallback
