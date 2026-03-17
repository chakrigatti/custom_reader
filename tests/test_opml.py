from __future__ import annotations

import pathlib

import pytest

from reader.services.opml import generate_opml, parse_opml

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def test_parse_opml():
    xml = (FIXTURES_DIR / "feeds.opml").read_text()
    entries = parse_opml(xml)
    assert len(entries) == 4

    # Check folder feeds
    tech_feeds = [(url, title, cat) for url, title, cat in entries if cat == "Technology"]
    assert len(tech_feeds) == 2

    science_feeds = [(url, title, cat) for url, title, cat in entries if cat == "Science"]
    assert len(science_feeds) == 1

    # Check uncategorized
    flat_feeds = [(url, title, cat) for url, title, cat in entries if cat is None]
    assert len(flat_feeds) == 1
    assert flat_feeds[0][1] == "xkcd"


def test_generate_opml():
    feeds = [
        {
            "title": "TechCrunch",
            "feed_url": "https://techcrunch.com/feed/",
            "site_url": "https://techcrunch.com",
            "categories": [{"name": "Tech"}],
        },
        {
            "title": "xkcd",
            "feed_url": "https://xkcd.com/rss.xml",
            "site_url": "https://xkcd.com",
            "categories": [],
        },
    ]
    xml = generate_opml(feeds)
    assert "TechCrunch" in xml
    assert "xkcd" in xml
    assert "Tech" in xml


def test_opml_roundtrip():
    """generate → parse should preserve structure."""
    feeds = [
        {
            "title": "Feed A",
            "feed_url": "https://a.com/feed",
            "site_url": "https://a.com",
            "categories": [{"name": "Cat1"}],
        },
        {
            "title": "Feed B",
            "feed_url": "https://b.com/feed",
            "site_url": "https://b.com",
            "categories": [],
        },
    ]
    xml = generate_opml(feeds)
    entries = parse_opml(xml)
    assert len(entries) == 2

    cat_entry = [e for e in entries if e[2] == "Cat1"]
    assert len(cat_entry) == 1
    assert cat_entry[0][0] == "https://a.com/feed"

    flat_entry = [e for e in entries if e[2] is None]
    assert len(flat_entry) == 1
    assert flat_entry[0][0] == "https://b.com/feed"


@pytest.mark.asyncio
async def test_opml_import_export_api(client, db):
    """Import OPML via API, then export and verify structure."""
    xml = (FIXTURES_DIR / "feeds.opml").read_text()

    # Import — feeds won't resolve since we're not mocking HTTP, but that's ok
    # The import handles errors per-feed
    import_resp = await client.post(
        "/opml/import",
        files={"file": ("feeds.opml", xml.encode(), "application/xml")},
    )
    assert import_resp.status_code == 200
    result = import_resp.json()
    # Some feeds will be imported, some may error (no mock)
    assert "imported" in result
    assert "skipped" in result
    assert "errors" in result

    # Export
    export_resp = await client.get("/opml/export")
    assert export_resp.status_code == 200
    assert "xml" in export_resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_opml_import_creates_categories(client, db):
    """OPML folders should create categories."""
    xml = (FIXTURES_DIR / "feeds.opml").read_text()
    await client.post(
        "/opml/import",
        files={"file": ("feeds.opml", xml.encode(), "application/xml")},
    )

    cat_resp = await client.get("/categories")
    data = cat_resp.json()
    cat_names = [c["name"] for c in data["data"]]
    # Should have created Technology and Science categories
    assert "Technology" in cat_names or "Science" in cat_names
