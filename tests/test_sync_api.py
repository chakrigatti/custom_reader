from __future__ import annotations

import pathlib

import httpx
import pytest
import respx

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


async def _create_feed(client: httpx.AsyncClient, url: str, rss_xml: str):
    """Helper to create a feed with mocked discovery."""
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            text=rss_xml,
            headers={"content-type": "application/rss+xml"},
        )
    )
    resp = await client.post("/feeds", json={"url": url})
    return resp.json()["id"]


@pytest.mark.asyncio
class TestSyncFeed:
    @respx.mock
    async def test_sync_creates_articles(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        feed_id = await _create_feed(
            client, "https://synctest.com/feed", rss_xml
        )

        # Mock the fetch for sync
        respx.get("https://synctest.com/feed").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )

        resp = await client.post(f"/feeds/{feed_id}/sync")
        assert resp.status_code == 200
        body = resp.json()
        assert body["fetched"] == 3
        assert body["feed_id"] == feed_id
        assert body["title"] == "Test Blog"

        # Verify articles were created
        articles = await client.get("/articles", params={"feed_id": feed_id})
        assert articles.json()["total"] == 3

    @respx.mock
    async def test_sync_deduplicates(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        feed_id = await _create_feed(
            client, "https://dedup.com/feed", rss_xml
        )

        # First sync
        respx.get("https://dedup.com/feed").mock(
            return_value=httpx.Response(200, text=rss_xml)
        )
        resp1 = await client.post(f"/feeds/{feed_id}/sync")
        assert resp1.json()["fetched"] == 3

        # Second sync — same articles, 0 new
        respx.get("https://dedup.com/feed").mock(
            return_value=httpx.Response(200, text=rss_xml)
        )
        resp2 = await client.post(f"/feeds/{feed_id}/sync")
        assert resp2.json()["fetched"] == 0

    @respx.mock
    async def test_sync_atom_feed(self, client: httpx.AsyncClient):
        atom_xml = _load("atom_standard.xml")
        feed_id = await _create_feed(
            client, "https://atomsync.com/atom.xml", atom_xml
        )

        respx.get("https://atomsync.com/atom.xml").mock(
            return_value=httpx.Response(200, text=atom_xml)
        )

        resp = await client.post(f"/feeds/{feed_id}/sync")
        assert resp.status_code == 200
        assert resp.json()["fetched"] == 2  # atom has 2 entries

    @respx.mock
    async def test_sync_minimal_rss(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_minimal.xml")
        feed_id = await _create_feed(
            client, "https://minimal.com/feed", rss_xml
        )

        respx.get("https://minimal.com/feed").mock(
            return_value=httpx.Response(200, text=rss_xml)
        )

        resp = await client.post(f"/feeds/{feed_id}/sync")
        assert resp.status_code == 200
        assert resp.json()["fetched"] == 2

    async def test_sync_bookmark_feed_422(self, client: httpx.AsyncClient):
        resp = await client.post("/feeds/1/sync")
        assert resp.status_code == 422

    async def test_sync_nonexistent_feed_404(self, client: httpx.AsyncClient):
        resp = await client.post("/feeds/9999/sync")
        assert resp.status_code == 404

    @respx.mock
    async def test_sync_upstream_error_502(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        feed_id = await _create_feed(
            client, "https://failing.com/feed", rss_xml
        )

        # Mock upstream failure
        respx.get("https://failing.com/feed").mock(
            return_value=httpx.Response(500)
        )

        resp = await client.post(f"/feeds/{feed_id}/sync")
        assert resp.status_code == 502


@pytest.mark.asyncio
class TestSyncAll:
    @respx.mock
    async def test_sync_all(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        feed_id = await _create_feed(
            client, "https://syncall.com/feed", rss_xml
        )

        respx.get("https://syncall.com/feed").mock(
            return_value=httpx.Response(200, text=rss_xml)
        )

        resp = await client.post("/sync")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        # Should have synced the feed we created (but not the bookmark sentinel)
        synced_ids = [r["feed_id"] for r in body["data"]]
        assert feed_id in synced_ids
        assert 1 not in synced_ids  # sentinel excluded

    @respx.mock
    async def test_sync_all_skips_bookmark(self, client: httpx.AsyncClient):
        resp = await client.post("/sync")
        assert resp.status_code == 200
        body = resp.json()
        synced_ids = [r["feed_id"] for r in body["data"]]
        assert 1 not in synced_ids

    @respx.mock
    async def test_sync_all_captures_errors(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        feed_id = await _create_feed(
            client, "https://errorall.com/feed", rss_xml
        )

        # Make the sync fail
        respx.get("https://errorall.com/feed").mock(
            return_value=httpx.Response(500)
        )

        resp = await client.post("/sync")
        assert resp.status_code == 200
        body = resp.json()
        # Should still have an entry for the failed feed with fetched=0
        for result in body["data"]:
            if result["feed_id"] == feed_id:
                assert result["fetched"] == 0
                break
        else:
            pytest.fail("Expected result for failed feed")
