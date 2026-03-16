from __future__ import annotations

import pathlib

import pytest
import httpx
import respx

from reader.services.discovery import detect_source_type

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


@pytest.mark.asyncio
class TestDetectSourceType:
    async def test_rss_url(self):
        rss_xml = _load("rss_standard.xml")
        with respx.mock:
            respx.get("https://testblog.com/feed.xml").mock(
                return_value=httpx.Response(
                    200,
                    text=rss_xml,
                    headers={"content-type": "application/rss+xml"},
                )
            )

            source_type, feed_url, title, site_url = await detect_source_type(
                "https://testblog.com/feed.xml"
            )
            assert source_type == "rss"
            assert feed_url == "https://testblog.com/feed.xml"
            assert title == "Test Blog"

    async def test_atom_url(self):
        atom_xml = _load("atom_standard.xml")
        with respx.mock:
            respx.get("https://atomtest.com/atom.xml").mock(
                return_value=httpx.Response(
                    200,
                    text=atom_xml,
                    headers={"content-type": "application/atom+xml"},
                )
            )

            source_type, feed_url, title, site_url = await detect_source_type(
                "https://atomtest.com/atom.xml"
            )
            assert source_type == "rss"
            assert title == "Atom Test Feed"

    async def test_blog_with_link_tag(self):
        blog_html = _load("blog_with_link.html")
        rss_xml = _load("rss_standard.xml")
        with respx.mock:
            respx.get(url__eq="https://myblog.com").mock(
                return_value=httpx.Response(
                    200,
                    text=blog_html,
                    headers={"content-type": "text/html"},
                )
            )
            respx.get(url__eq="https://myblog.com/feed.xml").mock(
                return_value=httpx.Response(
                    200,
                    text=rss_xml,
                    headers={"content-type": "application/rss+xml"},
                )
            )

            source_type, feed_url, title, site_url = await detect_source_type(
                "https://myblog.com"
            )
            assert source_type == "blog"
            assert feed_url == "https://myblog.com/feed.xml"
            assert title == "Test Blog"
            assert site_url == "https://myblog.com"

    async def test_blog_with_fallback_path(self):
        blog_html = _load("blog_no_link.html")
        rss_xml = _load("rss_standard.xml")
        with respx.mock:
            respx.get(url__eq="https://fallback.com").mock(
                return_value=httpx.Response(
                    200,
                    text=blog_html,
                    headers={"content-type": "text/html"},
                )
            )
            # First few fallback paths fail
            respx.get(url__eq="https://fallback.com/feed").mock(
                return_value=httpx.Response(404, text="Not Found")
            )
            respx.get(url__eq="https://fallback.com/rss").mock(
                return_value=httpx.Response(404, text="Not Found")
            )
            # /atom.xml succeeds
            respx.get(url__eq="https://fallback.com/atom.xml").mock(
                return_value=httpx.Response(
                    200,
                    text=rss_xml,
                    headers={"content-type": "application/rss+xml"},
                )
            )
            # Remaining fallback paths (shouldn't be reached)
            respx.get(url__eq="https://fallback.com/feed.xml").mock(
                return_value=httpx.Response(404, text="Not Found")
            )
            respx.get(url__eq="https://fallback.com/index.xml").mock(
                return_value=httpx.Response(404, text="Not Found")
            )

            source_type, feed_url, title, site_url = await detect_source_type(
                "https://fallback.com"
            )
            assert source_type == "blog"
            assert feed_url == "https://fallback.com/atom.xml"

    async def test_nitter_handle(self):
        source_type, feed_url, title, site_url = await detect_source_type(
            "@testuser"
        )
        assert source_type == "nitter"
        assert "/testuser/rss" in feed_url
        assert title == "@testuser"

    async def test_twitter_url(self):
        source_type, feed_url, title, site_url = await detect_source_type(
            "https://twitter.com/someone"
        )
        assert source_type == "nitter"
        assert "/someone/rss" in feed_url

    async def test_unresolvable_url(self):
        blog_html = _load("blog_no_link.html")
        with respx.mock:
            respx.get(url__eq="https://nofeed.example.com").mock(
                return_value=httpx.Response(
                    200,
                    text=blog_html,
                    headers={"content-type": "text/html"},
                )
            )
            # All fallback paths fail
            for path in ["/feed", "/rss", "/atom.xml", "/feed.xml", "/index.xml"]:
                respx.get(url__eq=f"https://nofeed.example.com{path}").mock(
                    return_value=httpx.Response(404, text="Not Found")
                )

            from reader.errors import APIError

            with pytest.raises(APIError) as exc_info:
                await detect_source_type("https://nofeed.example.com")
            assert exc_info.value.status == 422

    async def test_unreachable_url(self):
        with respx.mock:
            respx.get("https://unreachable.example.com").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            from reader.errors import APIError

            with pytest.raises(APIError) as exc_info:
                await detect_source_type("https://unreachable.example.com")
            assert exc_info.value.status == 422
