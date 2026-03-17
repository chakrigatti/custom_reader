from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


async def fetch_favicon_url(site_url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
            # Try /favicon.ico first
            favicon_ico = urljoin(site_url, "/favicon.ico")
            try:
                resp = await client.head(favicon_ico)
                ct = resp.headers.get("content-type", "")
                if resp.status_code == 200 and "image" in ct:
                    return favicon_ico
            except httpx.HTTPError:
                pass

            # Parse HTML for link tags
            try:
                resp = await client.get(site_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for rel in ("icon", "shortcut icon"):
                        link = soup.find("link", rel=lambda r: r and rel in r)
                        if link and link.get("href"):
                            return urljoin(site_url, link["href"])
            except httpx.HTTPError:
                pass

    except Exception:
        pass

    return None
