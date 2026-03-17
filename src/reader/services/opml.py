from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reader.models.db import Feed
from reader.models.schemas import OPMLImportResult


def parse_opml(xml: str) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """Parse OPML XML into a list of (feed_url, title, category_name)."""
    root = ET.fromstring(xml)
    body = root.find("body")
    if body is None:
        return []

    entries: List[Tuple[str, Optional[str], Optional[str]]] = []

    for outline in body:
        xml_url = outline.get("xmlUrl")
        if xml_url:
            # Top-level feed (no category)
            entries.append((xml_url, outline.get("title") or outline.get("text"), None))
        else:
            # Folder — children are feeds
            folder_name = outline.get("title") or outline.get("text")
            for child in outline:
                child_url = child.get("xmlUrl")
                if child_url:
                    entries.append((
                        child_url,
                        child.get("title") or child.get("text"),
                        folder_name,
                    ))

    return entries


def generate_opml(feeds_with_categories: List[dict]) -> str:
    """Generate OPML 2.0 XML from a list of feed dicts with categories."""
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    title_el = ET.SubElement(head, "title")
    title_el.text = "Reader Subscriptions"
    body = ET.SubElement(root, "body")

    # Group by category
    folders: dict[str, list] = {}
    uncategorized: list = []

    for feed in feeds_with_categories:
        cats = feed.get("categories", [])
        if cats:
            for cat in cats:
                cat_name = cat["name"]
                if cat_name not in folders:
                    folders[cat_name] = []
                folders[cat_name].append(feed)
        else:
            uncategorized.append(feed)

    # Emit folder outlines
    for folder_name in sorted(folders.keys()):
        folder_el = ET.SubElement(body, "outline", text=folder_name, title=folder_name)
        for feed in folders[folder_name]:
            ET.SubElement(
                folder_el,
                "outline",
                type="rss",
                text=feed["title"],
                title=feed["title"],
                xmlUrl=feed["feed_url"],
                htmlUrl=feed.get("site_url", ""),
            )

    # Emit uncategorized feeds
    for feed in uncategorized:
        ET.SubElement(
            body,
            "outline",
            type="rss",
            text=feed["title"],
            title=feed["title"],
            xmlUrl=feed["feed_url"],
            htmlUrl=feed.get("site_url", ""),
        )

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


async def import_opml(db: AsyncSession, xml: str) -> OPMLImportResult:
    from reader.services.categories import get_or_create_category
    from reader.services.discovery import detect_source_type

    entries = parse_opml(xml)
    imported = 0
    skipped = 0
    errors: List[str] = []

    for feed_url, title, category_name in entries:
        try:
            # Check if feed already exists
            existing = await db.execute(select(Feed).where(Feed.feed_url == feed_url))
            feed = existing.scalar_one_or_none()

            if feed:
                # Still assign category if provided
                if category_name:
                    category = await get_or_create_category(db, category_name)
                    result = await db.execute(
                        select(Feed)
                        .where(Feed.id == feed.id)
                        .options(selectinload(Feed.categories))
                    )
                    feed = result.scalar_one()
                    if category not in feed.categories:
                        feed.categories.append(category)
                skipped += 1
                continue

            # Try to detect source type, but fall back to using raw URL
            try:
                source_type, resolved_url, resolved_title, site_url = (
                    await detect_source_type(feed_url)
                )
            except Exception:
                # Use the URL as-is
                resolved_url = feed_url
                resolved_title = title or feed_url
                site_url = feed_url
                source_type = "rss"

            # Check again with resolved URL
            existing = await db.execute(
                select(Feed).where(Feed.feed_url == resolved_url)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            feed = Feed(
                title=resolved_title or title or feed_url,
                feed_url=resolved_url,
                site_url=site_url,
                source_type=source_type,
            )
            db.add(feed)
            await db.flush()

            if category_name:
                category = await get_or_create_category(db, category_name)
                feed.categories.append(category)

            imported += 1

        except Exception as e:
            errors.append(f"{feed_url}: {e}")

    await db.commit()
    return OPMLImportResult(imported=imported, skipped=skipped, errors=errors)


async def export_opml(db: AsyncSession) -> str:
    result = await db.execute(
        select(Feed)
        .where(Feed.id != 1)  # Exclude sentinel bookmark feed
        .options(selectinload(Feed.categories))
        .order_by(Feed.title)
    )
    feeds = result.scalars().all()

    feeds_data = []
    for feed in feeds:
        feeds_data.append({
            "title": feed.title,
            "feed_url": feed.feed_url,
            "site_url": feed.site_url,
            "categories": [{"name": c.name} for c in feed.categories],
        })

    return generate_opml(feeds_data)
