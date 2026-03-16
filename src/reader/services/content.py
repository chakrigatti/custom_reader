from __future__ import annotations

from typing import Optional, Tuple

import trafilatura
from markdownify import markdownify


def extract_content(
    html: str, url: str
) -> Tuple[Optional[str], str, str, Optional[str], Optional[str], Optional[str]]:
    """Extract content from an HTML page.

    Returns (title, content_html, content_markdown, summary, author, warning).
    """
    metadata = trafilatura.extract_metadata(html, default_url=url)
    title = metadata.title if metadata else None
    author = metadata.author if metadata else None

    extracted_html = trafilatura.extract(
        html, output_format="html", include_links=True
    )
    warning = None

    if extracted_html:
        content_html = extracted_html
        content_markdown = markdownify(content_html, strip=["img"])
    else:
        content_html = ""
        content_markdown = ""
        warning = "Could not extract article content. The page may be paywalled or JavaScript-rendered."

    summary = None
    extracted_text = trafilatura.extract(html)
    if extracted_text:
        summary = (
            extracted_text[:300].rsplit(" ", 1)[0]
            if len(extracted_text) > 300
            else extracted_text
        )

    return title, content_html, content_markdown, summary, author, warning


def extract_from_feed_entry(
    entry,
) -> Tuple[str, str, str, Optional[str], Optional[str]]:
    """Extract content from a feedparser entry.

    Returns (title, content_html, content_markdown, summary, author).
    """
    title = entry.get("title", "")

    content_html = ""
    if "content" in entry and entry.content:
        content_html = entry.content[0].get("value", "")
    elif "summary_detail" in entry:
        content_html = entry.summary_detail.get("value", "")
    elif "summary" in entry:
        content_html = entry.get("summary", "")

    content_markdown = markdownify(content_html, strip=["img"]) if content_html else ""

    summary = entry.get("summary")
    if summary and len(summary) > 300:
        summary = summary[:300].rsplit(" ", 1)[0]

    author = entry.get("author")

    return title, content_html, content_markdown, summary, author
