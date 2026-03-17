from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_tag(client):
    resp = await client.post("/tags", json={"name": "python"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "python"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_tag(client):
    await client.post("/tags", json={"name": "python"})
    resp = await client.post("/tags", json={"name": "python"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_tags(client):
    await client.post("/tags", json={"name": "alpha"})
    await client.post("/tags", json={"name": "beta"})
    resp = await client.get("/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_tags_with_query(client):
    await client.post("/tags", json={"name": "python"})
    await client.post("/tags", json={"name": "javascript"})
    resp = await client.get("/tags?q=pyth")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["name"] == "python"


@pytest.mark.asyncio
async def test_delete_tag(client):
    create = await client.post("/tags", json={"name": "todelete"})
    tag_id = create.json()["id"]
    resp = await client.delete(f"/tags/{tag_id}")
    assert resp.status_code == 204

    resp = await client.delete(f"/tags/{tag_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_tag_to_article(client, db):
    from reader.models.db import Article

    article = Article(
        feed_id=1,
        title="Test Article",
        url="https://example.com/tag-test",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    resp = await client.post(
        f"/articles/{article.id}/tags", json={"name": "python"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "python"


@pytest.mark.asyncio
async def test_remove_tag_from_article(client, db):
    from reader.models.db import Article

    article = Article(
        feed_id=1,
        title="Tag Remove Test",
        url="https://example.com/tag-remove",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    add_resp = await client.post(
        f"/articles/{article.id}/tags", json={"name": "removeme"}
    )
    tag_id = add_resp.json()["tags"][0]["id"]

    resp = await client.delete(f"/articles/{article.id}/tags/{tag_id}")
    assert resp.status_code == 200
    assert len(resp.json()["tags"]) == 0


@pytest.mark.asyncio
async def test_filter_articles_by_tag(client, db):
    from reader.models.db import Article

    article = Article(
        feed_id=1,
        title="Tagged Article",
        url="https://example.com/tagged",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    await client.post(f"/articles/{article.id}/tags", json={"name": "special"})

    resp = await client.get("/articles?tag=special")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["title"] == "Tagged Article"


@pytest.mark.asyncio
async def test_article_response_includes_tags(client, db):
    from reader.models.db import Article

    article = Article(
        feed_id=1,
        title="Tags Included",
        url="https://example.com/tags-included",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    resp = await client.get(f"/articles/{article.id}")
    assert resp.status_code == 200
    assert "tags" in resp.json()
    assert resp.json()["tags"] == []


@pytest.mark.asyncio
async def test_delete_article_cascades_junction(client, db):
    from sqlalchemy import select, text

    from reader.models.db import Article

    article = Article(
        feed_id=1,
        title="Cascade Test",
        url="https://example.com/cascade",
        content_html="<p>test</p>",
        content_markdown="test",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    await client.post(f"/articles/{article.id}/tags", json={"name": "persist"})

    # Delete the article directly
    await db.delete(article)
    await db.commit()

    # Tag should still exist
    resp = await client.get("/tags?q=persist")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
