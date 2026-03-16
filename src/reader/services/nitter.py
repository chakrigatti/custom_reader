from __future__ import annotations

from urllib.parse import urlparse


def is_nitter_or_handle(url: str) -> bool:
    if url.startswith("@"):
        return True
    parsed = urlparse(url)
    return parsed.hostname in (
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "www.x.com",
        "nitter.net",
    )


def to_nitter_rss(url: str, nitter_instance: str) -> str:
    nitter_instance = nitter_instance.rstrip("/")

    if url.startswith("@"):
        username = url.lstrip("@")
        return "{}/{}/rss".format(nitter_instance, username)

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    username = path.split("/")[0] if path else ""
    if not username:
        raise ValueError("Cannot extract username from URL: {}".format(url))

    return "{}/{}/rss".format(nitter_instance, username)
