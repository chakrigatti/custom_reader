from __future__ import annotations

import pathlib

import httpx
import pytest
import respx

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


@pytest.mark.asyncio
class TestSaveBookmark:
    @respx.mock
    async def test_save_bookmark_201(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/article").mock(
            return_value=httpx.Response(200, text=html)
        )

        resp = await client.post(
            "/articles", json={"url": "https://example.com/article"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["feed_id"] == 1
        assert body["url"] == "https://example.com/article"
        assert "id" in body
        assert "Location" in resp.headers
        assert f"/articles/{body['id']}" in resp.headers["Location"]

    @respx.mock
    async def test_save_bookmark_empty_extraction_warning(
        self, client: httpx.AsyncClient
    ):
        html = _load("article_empty.html")
        respx.get("https://example.com/login-wall").mock(
            return_value=httpx.Response(200, text=html)
        )

        resp = await client.post(
            "/articles", json={"url": "https://example.com/login-wall"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["warning"] is not None
        assert body["content_html"] == ""
        assert body["content_markdown"] == ""

    @respx.mock
    async def test_duplicate_bookmark_409(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/dup-article").mock(
            return_value=httpx.Response(200, text=html)
        )

        await client.post(
            "/articles", json={"url": "https://example.com/dup-article"}
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/dup-article"}
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "existing_id" in body

    async def test_invalid_scheme_422(self, client: httpx.AsyncClient):
        resp = await client.post(
            "/articles", json={"url": "ftp://example.com/file"}
        )
        # Pydantic's HttpUrl will reject ftp:// at validation level → 422
        assert resp.status_code == 422

    @respx.mock
    async def test_save_bookmark_fetch_error_502(self, client: httpx.AsyncClient):
        respx.get("https://example.com/unreachable").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        resp = await client.post(
            "/articles", json={"url": "https://example.com/unreachable"}
        )
        assert resp.status_code == 502


@pytest.mark.asyncio
class TestListArticles:
    @respx.mock
    async def test_list_articles(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        for i in range(3):
            respx.get(f"https://example.com/art-{i}").mock(
                return_value=httpx.Response(200, text=html)
            )
            await client.post(
                "/articles", json={"url": f"https://example.com/art-{i}"}
            )

        resp = await client.get("/articles")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["data"]) == 3

    @respx.mock
    async def test_filter_by_source_bookmark(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/bm-filter").mock(
            return_value=httpx.Response(200, text=html)
        )
        await client.post(
            "/articles", json={"url": "https://example.com/bm-filter"}
        )

        resp = await client.get("/articles", params={"source": "bookmark"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        for art in body["data"]:
            assert art["feed_id"] == 1

    async def test_source_and_feed_id_together_422(self, client: httpx.AsyncClient):
        resp = await client.get(
            "/articles", params={"source": "bookmark", "feed_id": 2}
        )
        assert resp.status_code == 422

    @respx.mock
    async def test_pagination(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        for i in range(5):
            respx.get(f"https://example.com/page-{i}").mock(
                return_value=httpx.Response(200, text=html)
            )
            await client.post(
                "/articles", json={"url": f"https://example.com/page-{i}"}
            )

        resp = await client.get("/articles", params={"limit": 2, "offset": 0})
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["total"] == 5

        resp2 = await client.get("/articles", params={"limit": 2, "offset": 4})
        body2 = resp2.json()
        assert len(body2["data"]) == 1

    @respx.mock
    async def test_filter_by_state(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/state-art").mock(
            return_value=httpx.Response(200, text=html)
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/state-art"}
        )
        art_id = resp.json()["id"]

        # All articles are "unread" by default
        resp = await client.get("/articles", params={"state": "unread"})
        assert resp.json()["total"] >= 1

        resp = await client.get("/articles", params={"state": "read"})
        assert resp.json()["total"] == 0


@pytest.mark.asyncio
class TestGetArticle:
    @respx.mock
    async def test_get_article_json(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/get-art").mock(
            return_value=httpx.Response(200, text=html)
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/get-art"}
        )
        art_id = resp.json()["id"]

        resp = await client.get(
            f"/articles/{art_id}",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == art_id
        assert "content_markdown" in body

    @respx.mock
    async def test_get_article_markdown(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/md-art").mock(
            return_value=httpx.Response(200, text=html)
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/md-art"}
        )
        art_id = resp.json()["id"]

        resp = await client.get(
            f"/articles/{art_id}",
            headers={"Accept": "text/markdown"},
        )
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]

    @respx.mock
    async def test_get_article_not_acceptable_406(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/406-art").mock(
            return_value=httpx.Response(200, text=html)
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/406-art"}
        )
        art_id = resp.json()["id"]

        resp = await client.get(
            f"/articles/{art_id}",
            headers={"Accept": "text/xml"},
        )
        assert resp.status_code == 406

    async def test_get_article_404(self, client: httpx.AsyncClient):
        resp = await client.get("/articles/9999")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestUpdateArticle:
    @respx.mock
    async def test_patch_state(self, client: httpx.AsyncClient):
        html = _load("article_normal.html")
        respx.get("https://example.com/patch-art").mock(
            return_value=httpx.Response(200, text=html)
        )
        resp = await client.post(
            "/articles", json={"url": "https://example.com/patch-art"}
        )
        art_id = resp.json()["id"]

        resp = await client.patch(
            f"/articles/{art_id}", json={"state": "read"}
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "read"

        # Patch to read_again
        resp = await client.patch(
            f"/articles/{art_id}", json={"state": "read_again"}
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "read_again"

    async def test_patch_invalid_state_422(self, client: httpx.AsyncClient):
        resp = await client.patch(
            "/articles/1", json={"state": "invalid_state"}
        )
        assert resp.status_code == 422

    async def test_patch_nonexistent_404(self, client: httpx.AsyncClient):
        resp = await client.patch(
            "/articles/9999", json={"state": "read"}
        )
        assert resp.status_code == 404
