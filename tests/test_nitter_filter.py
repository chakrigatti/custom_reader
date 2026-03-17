from __future__ import annotations

import pathlib
import time

import feedparser
import pytest

from reader.services.nitter_filter import (
    consolidate_threads,
    extract_username_from_feed_url,
    filter_nitter_entries,
)

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


# --- extract_username_from_feed_url ---


class TestExtractUsername:
    def test_standard_nitter_url(self):
        assert (
            extract_username_from_feed_url("https://nitter.net/elonmusk/rss")
            == "elonmusk"
        )

    def test_custom_instance(self):
        assert (
            extract_username_from_feed_url("https://nitter.example.com/testuser/rss")
            == "testuser"
        )

    def test_trailing_slash(self):
        assert (
            extract_username_from_feed_url("https://nitter.net/jack/rss/")
            == "jack"
        )

    def test_no_username_raises(self):
        with pytest.raises(ValueError):
            extract_username_from_feed_url("https://nitter.net/")


# --- filter_nitter_entries ---


def _make_entry(title: str, author: str = "@testuser", link: str = "") -> dict:
    return {"title": title, "author": author, "link": link}


class TestFilterNitterEntries:
    def test_filter_removes_retweets(self):
        entries = [
            _make_entry("Hello world"),
            _make_entry("RT @other: some retweet", author="@other"),
        ]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 1
        assert result[0]["title"] == "Hello world"

    def test_filter_removes_replies(self):
        entries = [
            _make_entry("Hello world"),
            _make_entry("@someone I disagree"),
        ]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 1
        assert result[0]["title"] == "Hello world"

    def test_filter_keeps_original_posts(self):
        entries = [
            _make_entry("Original post 1"),
            _make_entry("Original post 2"),
        ]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 2

    def test_filter_removes_other_authors(self):
        entries = [
            _make_entry("My post", author="@testuser"),
            _make_entry("Not my post", author="@someone_else"),
        ]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 1
        assert result[0]["title"] == "My post"

    def test_filter_case_insensitive_author(self):
        entries = [_make_entry("My post", author="@TestUser")]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 1

    def test_filter_empty_author_passes(self):
        entries = [_make_entry("Post without author", author="")]
        result = filter_nitter_entries(entries, "testuser")
        assert len(result) == 1


# --- consolidate_threads ---


def _make_thread_entry(
    title: str, status_id: str, html: str, pub_time: tuple, author: str = "@testuser"
) -> dict:
    return {
        "title": title,
        "link": f"https://nitter.example.com/testuser/status/{status_id}",
        "summary_detail": {"value": html},
        "summary": html,
        "published_parsed": pub_time,
        "author": author,
    }


class TestConsolidateThreads:
    def test_consolidate_single_tweets(self):
        t1 = time.strptime("2026-03-10 10:00:00", "%Y-%m-%d %H:%M:%S")
        t2 = time.strptime("2026-03-10 11:00:00", "%Y-%m-%d %H:%M:%S")
        entries = [
            _make_thread_entry("Tweet A", "1001", "<p>Tweet A</p>", t1),
            _make_thread_entry("Tweet B", "1002", "<p>Tweet B</p>", t2),
        ]
        result = consolidate_threads(entries, "testuser")
        assert len(result) == 2
        # Single tweets should not have [thread] suffix
        assert "[thread]" not in result[0]["title"]
        assert "[thread]" not in result[1]["title"]

    def test_consolidate_threads(self):
        t1 = time.strptime("2026-03-10 14:00:00", "%Y-%m-%d %H:%M:%S")
        t2 = time.strptime("2026-03-10 14:01:00", "%Y-%m-%d %H:%M:%S")
        t3 = time.strptime("2026-03-10 14:02:00", "%Y-%m-%d %H:%M:%S")
        entries = [
            _make_thread_entry("Part 1", "3001", "<p>Part 1</p>", t1),
            _make_thread_entry(
                "Part 2",
                "3002",
                '<p>Part 2</p><p>Replying to <a href="/testuser/status/3001">@testuser</a></p>',
                t2,
            ),
            _make_thread_entry(
                "Part 3",
                "3003",
                '<p>Part 3</p><p>Replying to <a href="/testuser/status/3002">@testuser</a></p>',
                t3,
            ),
        ]
        result = consolidate_threads(entries, "testuser")
        assert len(result) == 1
        merged = result[0]
        assert merged["title"] == "Part 1 [thread]"
        assert merged["link"] == "https://nitter.example.com/testuser/status/3001"
        assert "<hr>" in merged["summary_detail"]["value"]
        assert "Part 1" in merged["summary_detail"]["value"]
        assert "Part 2" in merged["summary_detail"]["value"]
        assert "Part 3" in merged["summary_detail"]["value"]

    def test_consolidate_mixed(self):
        """Standalone tweet + thread should produce 2 entries."""
        t1 = time.strptime("2026-03-10 10:00:00", "%Y-%m-%d %H:%M:%S")
        t2 = time.strptime("2026-03-10 14:00:00", "%Y-%m-%d %H:%M:%S")
        t3 = time.strptime("2026-03-10 14:01:00", "%Y-%m-%d %H:%M:%S")
        entries = [
            _make_thread_entry("Standalone", "1001", "<p>Standalone</p>", t1),
            _make_thread_entry("Thread 1", "3001", "<p>Thread 1</p>", t2),
            _make_thread_entry(
                "Thread 2",
                "3002",
                '<p>Thread 2</p><a href="/testuser/status/3001">link</a>',
                t3,
            ),
        ]
        result = consolidate_threads(entries, "testuser")
        assert len(result) == 2
        assert result[0]["title"] == "Standalone"
        assert result[1]["title"] == "Thread 1 [thread]"


# --- Integration: parse fixture XML through full pipeline ---


class TestNitterFixtureIntegration:
    def test_full_pipeline(self):
        xml = _load("nitter_feed.xml")
        parsed = feedparser.parse(xml)

        entries = filter_nitter_entries(parsed.entries, "testuser")
        # Should have filtered out 1 retweet + 1 reply = 5 remaining
        assert len(entries) == 5

        result = consolidate_threads(entries, "testuser")
        # 2 standalone tweets + 1 thread (3 tweets merged) = 3 entries
        assert len(result) == 3

        titles = [e["title"] for e in result]
        # Check standalone tweets are present
        assert "This is my first original tweet about AI" in titles
        assert "Another great day for open source" in titles

        # Check thread is merged
        thread_entry = [e for e in result if "[thread]" in e["title"]][0]
        assert thread_entry["title"].startswith("Let me explain how RSS readers work")
        assert "<hr>" in thread_entry["summary_detail"]["value"]
