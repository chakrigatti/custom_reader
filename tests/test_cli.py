from __future__ import annotations

import json

import httpx
import pytest
import respx
from click.testing import CliRunner

from reader.cli import cli

runner = CliRunner()


@respx.mock
def test_add_feed():
    respx.post("http://localhost:8000/feeds").mock(
        return_value=httpx.Response(
            201,
            json={"id": 2, "title": "My Feed", "feed_url": "https://x.com/feed",
                  "site_url": "https://x.com", "source_type": "rss",
                  "created_at": "2024-01-01T00:00:00", "last_fetched_at": None},
        )
    )
    result = runner.invoke(cli, ["add", "https://x.com/feed"])
    assert result.exit_code == 0
    assert "My Feed" in result.output
    assert "#2" in result.output


@respx.mock
def test_add_feed_error():
    respx.post("http://localhost:8000/feeds").mock(
        return_value=httpx.Response(
            409, json={"status": 409, "detail": "Feed already exists", "existing_id": 2}
        )
    )
    result = runner.invoke(cli, ["add", "https://x.com/feed"])
    assert result.exit_code == 1
    assert "Feed already exists" in result.output


@respx.mock
def test_feeds_list():
    respx.get("http://localhost:8000/feeds").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 1, "title": "Saved Articles", "feed_url": "bookmark://saved",
                     "site_url": "bookmark://saved", "source_type": "bookmark",
                     "created_at": "2024-01-01T00:00:00", "last_fetched_at": None},
                    {"id": 2, "title": "Tech Blog", "feed_url": "https://tech.com/feed",
                     "site_url": "https://tech.com", "source_type": "rss",
                     "created_at": "2024-01-01T00:00:00", "last_fetched_at": "2024-01-02T12:00:00"},
                ],
                "total": 2,
                "limit": 50,
                "offset": 0,
            },
        )
    )
    result = runner.invoke(cli, ["feeds"])
    assert result.exit_code == 0
    assert "Saved Articles" in result.output
    assert "Tech Blog" in result.output
    assert "bookmark" in result.output


@respx.mock
def test_remove_feed():
    respx.delete("http://localhost:8000/feeds/2").mock(
        return_value=httpx.Response(204)
    )
    result = runner.invoke(cli, ["remove", "2"])
    assert result.exit_code == 0
    assert "Removed feed #2" in result.output


@respx.mock
def test_remove_sentinel_error():
    respx.delete("http://localhost:8000/feeds/1").mock(
        return_value=httpx.Response(
            403, json={"status": 403, "detail": "Cannot delete the sentinel feed"}
        )
    )
    result = runner.invoke(cli, ["remove", "1"])
    assert result.exit_code == 1
    assert "Cannot delete" in result.output


@respx.mock
def test_fetch_single_feed():
    respx.post("http://localhost:8000/feeds/2/sync").mock(
        return_value=httpx.Response(
            200,
            json={"fetched": 5, "feed_id": 2, "title": "Tech Blog"},
        )
    )
    result = runner.invoke(cli, ["fetch", "2"])
    assert result.exit_code == 0
    assert "5 new articles" in result.output
    assert "Tech Blog" in result.output


@respx.mock
def test_fetch_all():
    respx.post("http://localhost:8000/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"fetched": 3, "feed_id": 2, "title": "Tech Blog"},
                    {"fetched": 1, "feed_id": 3, "title": "News Feed"},
                ],
                "total": 2,
            },
        )
    )
    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code == 0
    assert "Tech Blog" in result.output
    assert "News Feed" in result.output
    assert "2 feeds synced" in result.output


@respx.mock
def test_save_bookmark():
    respx.post("http://localhost:8000/articles").mock(
        return_value=httpx.Response(
            201,
            json={"id": 10, "feed_id": 1, "title": "Saved Article", "url": "https://ex.com/a",
                  "author": None, "content_html": "<p>test</p>", "content_markdown": "test",
                  "summary": "test summary", "published_at": None,
                  "fetched_at": "2024-01-01T00:00:00", "state": "unread", "warning": None},
        )
    )
    result = runner.invoke(cli, ["save", "https://ex.com/a"])
    assert result.exit_code == 0
    assert "Saved article #10" in result.output
    assert "Saved Article" in result.output


@respx.mock
def test_save_bookmark_with_warning():
    respx.post("http://localhost:8000/articles").mock(
        return_value=httpx.Response(
            201,
            json={"id": 11, "feed_id": 1, "title": "https://ex.com/b",
                  "url": "https://ex.com/b", "author": None,
                  "content_html": "", "content_markdown": "",
                  "summary": None, "published_at": None,
                  "fetched_at": "2024-01-01T00:00:00", "state": "unread",
                  "warning": "Could not extract article content."},
        )
    )
    result = runner.invoke(cli, ["save", "https://ex.com/b"])
    assert result.exit_code == 0
    assert "Warning" in result.output


@respx.mock
def test_articles_list():
    respx.get("http://localhost:8000/articles").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": 1, "feed_id": 2, "title": "Article One", "url": "https://a.com/1",
                     "author": "Alice", "content_html": "", "content_markdown": "",
                     "summary": None, "published_at": "2024-01-01T12:00:00",
                     "fetched_at": "2024-01-02T00:00:00", "state": "unread", "warning": None},
                ],
                "total": 1,
                "limit": 50,
                "offset": 0,
            },
        )
    )
    result = runner.invoke(cli, ["articles"])
    assert result.exit_code == 0
    assert "Article One" in result.output
    assert "1 of 1" in result.output


@respx.mock
def test_articles_with_saved_flag():
    route = respx.get("http://localhost:8000/articles").mock(
        return_value=httpx.Response(
            200,
            json={"data": [], "total": 0, "limit": 50, "offset": 0},
        )
    )
    result = runner.invoke(cli, ["articles", "--saved"])
    assert result.exit_code == 0
    # Verify the request was made with source=bookmark
    assert route.calls[0].request.url.params["source"] == "bookmark"


@respx.mock
def test_read_article():
    respx.get("http://localhost:8000/articles/1").mock(
        return_value=httpx.Response(
            200,
            text="# Hello\n\nThis is the article content.",
            headers={"content-type": "text/markdown"},
        )
    )
    respx.patch("http://localhost:8000/articles/1").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "feed_id": 1, "title": "x", "url": "x",
                  "author": None, "content_html": "", "content_markdown": "",
                  "summary": None, "published_at": None,
                  "fetched_at": "2024-01-01T00:00:00", "state": "read",
                  "warning": None},
        )
    )
    result = runner.invoke(cli, ["read", "1"])
    assert result.exit_code == 0


@respx.mock
def test_mark_article():
    respx.patch("http://localhost:8000/articles/5").mock(
        return_value=httpx.Response(
            200,
            json={"id": 5, "feed_id": 1, "title": "x", "url": "x",
                  "author": None, "content_html": "", "content_markdown": "",
                  "summary": None, "published_at": None,
                  "fetched_at": "2024-01-01T00:00:00", "state": "read_again",
                  "warning": None},
        )
    )
    result = runner.invoke(cli, ["mark", "5", "read_again"])
    assert result.exit_code == 0
    assert "Marked article #5 as read_again" in result.output


@respx.mock
def test_mark_invalid_state():
    """Click should reject invalid state choices before HTTP call."""
    result = runner.invoke(cli, ["mark", "5", "deleted"])
    assert result.exit_code != 0
