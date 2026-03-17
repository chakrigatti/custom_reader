from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_category(client):
    resp = await client.post("/categories", json={"name": "Tech"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Tech"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_category(client):
    await client.post("/categories", json={"name": "Tech"})
    resp = await client.post("/categories", json={"name": "Tech"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_categories(client):
    await client.post("/categories", json={"name": "A"})
    await client.post("/categories", json={"name": "B"})
    resp = await client.get("/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_rename_category(client):
    create = await client.post("/categories", json={"name": "Old"})
    cat_id = create.json()["id"]
    resp = await client.patch(f"/categories/{cat_id}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_category(client):
    create = await client.post("/categories", json={"name": "ToDelete"})
    cat_id = create.json()["id"]
    resp = await client.delete(f"/categories/{cat_id}")
    assert resp.status_code == 204

    resp = await client.delete(f"/categories/{cat_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_set_feed_categories(client, db):
    from reader.models.db import Feed

    feed = Feed(
        title="Test Feed",
        feed_url="https://example.com/feed.xml",
        site_url="https://example.com",
        source_type="rss",
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    cat1 = await client.post("/categories", json={"name": "Cat1"})
    cat2 = await client.post("/categories", json={"name": "Cat2"})

    resp = await client.put(
        f"/feeds/{feed.id}/categories",
        json={"category_ids": [cat1.json()["id"], cat2.json()["id"]]},
    )
    assert resp.status_code == 200
    data = resp.json()
    cat_names = sorted([c["name"] for c in data["categories"]])
    assert cat_names == ["Cat1", "Cat2"]


@pytest.mark.asyncio
async def test_feed_response_includes_categories(client, db):
    from reader.models.db import Feed

    feed = Feed(
        title="Test Feed",
        feed_url="https://example.com/feed2.xml",
        site_url="https://example.com",
        source_type="rss",
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    resp = await client.get(f"/feeds/{feed.id}")
    assert resp.status_code == 200
    assert "categories" in resp.json()
    assert resp.json()["categories"] == []


@pytest.mark.asyncio
async def test_filter_articles_by_category(client, db):
    from reader.models.db import Article, Feed

    # Create feed via DB
    feed = Feed(
        title="Categorized Feed",
        feed_url="https://example.com/cat-feed.xml",
        site_url="https://example.com",
        source_type="rss",
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    # Create category via API
    cat_resp = await client.post("/categories", json={"name": "TestCat"})
    cat_id = cat_resp.json()["id"]

    # Assign category to feed via API
    await client.put(
        f"/feeds/{feed.id}/categories",
        json={"category_ids": [cat_id]},
    )

    # Create article
    article = Article(
        feed_id=feed.id,
        title="Cat Article",
        url="https://example.com/cat-article",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()

    resp = await client.get(f"/articles?category_id={cat_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["title"] == "Cat Article"


@pytest.mark.asyncio
async def test_delete_category_preserves_feeds(client, db):
    from reader.models.db import Feed

    feed = Feed(
        title="Keep Me",
        feed_url="https://example.com/keep.xml",
        site_url="https://example.com",
        source_type="rss",
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    cat = await client.post("/categories", json={"name": "Deletable"})
    cat_id = cat.json()["id"]

    await client.put(
        f"/feeds/{feed.id}/categories",
        json={"category_ids": [cat_id]},
    )

    await client.delete(f"/categories/{cat_id}")

    # Feed should still exist
    resp = await client.get(f"/feeds/{feed.id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Keep Me"
