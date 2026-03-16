from __future__ import annotations

import pathlib

import httpx
import pytest
import respx

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


@pytest.mark.asyncio
class TestCreateFeed:
    @respx.mock
    async def test_create_feed_201(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        respx.get("https://testblog.com/feed.xml").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )

        resp = await client.post(
            "/feeds", json={"url": "https://testblog.com/feed.xml"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Test Blog"
        assert body["source_type"] == "rss"
        assert body["feed_url"] == "https://testblog.com/feed.xml"
        assert "id" in body
        assert "Location" in resp.headers
        assert f"/feeds/{body['id']}" in resp.headers["Location"]

    @respx.mock
    async def test_duplicate_feed_409(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        respx.get("https://testblog.com/feed.xml").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )

        await client.post("/feeds", json={"url": "https://testblog.com/feed.xml"})
        resp = await client.post(
            "/feeds", json={"url": "https://testblog.com/feed.xml"}
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "existing_id" in body


@pytest.mark.asyncio
class TestListFeeds:
    async def test_list_feeds_includes_sentinel(self, client: httpx.AsyncClient):
        resp = await client.get("/feeds")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert body["limit"] == 50
        assert body["offset"] == 0
        # Sentinel feed should always be present
        feed_ids = [f["id"] for f in body["data"]]
        assert 1 in feed_ids

    @respx.mock
    async def test_list_feeds_pagination(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        # Create 3 feeds
        for i in range(3):
            respx.get(f"https://blog{i}.com/feed").mock(
                return_value=httpx.Response(
                    200,
                    text=rss_xml.replace("Test Blog", f"Blog {i}").replace(
                        "https://testblog.com", f"https://blog{i}.com"
                    ),
                    headers={"content-type": "application/rss+xml"},
                )
            )
            await client.post("/feeds", json={"url": f"https://blog{i}.com/feed"})

        resp = await client.get("/feeds", params={"limit": 2, "offset": 0})
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["total"] == 4  # sentinel + 3 created

        resp2 = await client.get("/feeds", params={"limit": 2, "offset": 2})
        body2 = resp2.json()
        assert len(body2["data"]) == 2
        assert body2["total"] == 4


@pytest.mark.asyncio
class TestGetFeed:
    async def test_get_sentinel_feed(self, client: httpx.AsyncClient):
        resp = await client.get("/feeds/1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 1
        assert body["source_type"] == "bookmark"

    async def test_get_feed_404(self, client: httpx.AsyncClient):
        resp = await client.get("/feeds/9999")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestDeleteFeed:
    @respx.mock
    async def test_delete_feed_204(self, client: httpx.AsyncClient):
        rss_xml = _load("rss_standard.xml")
        respx.get("https://deleteme.com/feed").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )
        resp = await client.post(
            "/feeds", json={"url": "https://deleteme.com/feed"}
        )
        feed_id = resp.json()["id"]

        del_resp = await client.delete(f"/feeds/{feed_id}")
        assert del_resp.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/feeds/{feed_id}")
        assert get_resp.status_code == 404

    async def test_delete_sentinel_403(self, client: httpx.AsyncClient):
        resp = await client.delete("/feeds/1")
        assert resp.status_code == 403

    async def test_delete_nonexistent_404(self, client: httpx.AsyncClient):
        resp = await client.delete("/feeds/9999")
        assert resp.status_code == 404

    @respx.mock
    async def test_delete_cascade(self, client: httpx.AsyncClient, db):
        """Deleting a feed should also delete its articles."""
        rss_xml = _load("rss_standard.xml")
        respx.get("https://cascade.com/feed").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )

        # Create feed
        resp = await client.post(
            "/feeds", json={"url": "https://cascade.com/feed"}
        )
        feed_id = resp.json()["id"]

        # Sync to create articles
        respx.get("https://cascade.com/feed").mock(
            return_value=httpx.Response(
                200,
                text=rss_xml,
                headers={"content-type": "application/rss+xml"},
            )
        )
        await client.post(f"/feeds/{feed_id}/sync")

        # Verify articles exist
        articles_resp = await client.get("/articles", params={"feed_id": feed_id})
        assert articles_resp.json()["total"] > 0

        # Delete feed
        await client.delete(f"/feeds/{feed_id}")

        # Verify articles are gone
        articles_resp = await client.get("/articles", params={"feed_id": feed_id})
        assert articles_resp.json()["total"] == 0
