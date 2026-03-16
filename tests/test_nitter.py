from __future__ import annotations

import pytest

from reader.services.nitter import is_nitter_or_handle, to_nitter_rss

NITTER_INSTANCE = "https://nitter.net"


class TestIsNitterOrHandle:
    def test_at_handle(self):
        assert is_nitter_or_handle("@elonmusk") is True

    def test_twitter_url(self):
        assert is_nitter_or_handle("https://twitter.com/elonmusk") is True

    def test_x_url(self):
        assert is_nitter_or_handle("https://x.com/elonmusk") is True

    def test_www_twitter(self):
        assert is_nitter_or_handle("https://www.twitter.com/someone") is True

    def test_www_x(self):
        assert is_nitter_or_handle("https://www.x.com/someone") is True

    def test_nitter_url(self):
        assert is_nitter_or_handle("https://nitter.net/someone") is True

    def test_regular_url(self):
        assert is_nitter_or_handle("https://example.com/feed") is False

    def test_random_string(self):
        assert is_nitter_or_handle("hello world") is False


class TestToNitterRss:
    def test_at_handle(self):
        result = to_nitter_rss("@elonmusk", NITTER_INSTANCE)
        assert result == "https://nitter.net/elonmusk/rss"

    def test_at_handle_double_at(self):
        result = to_nitter_rss("@@someone", NITTER_INSTANCE)
        assert result == "https://nitter.net/someone/rss"

    def test_twitter_url(self):
        result = to_nitter_rss("https://twitter.com/elonmusk", NITTER_INSTANCE)
        assert result == "https://nitter.net/elonmusk/rss"

    def test_x_url(self):
        result = to_nitter_rss("https://x.com/jack", NITTER_INSTANCE)
        assert result == "https://nitter.net/jack/rss"

    def test_nitter_url(self):
        result = to_nitter_rss("https://nitter.net/someone", NITTER_INSTANCE)
        assert result == "https://nitter.net/someone/rss"

    def test_url_with_trailing_slash(self):
        result = to_nitter_rss("https://twitter.com/user/", "https://nitter.net/")
        assert result == "https://nitter.net/user/rss"

    def test_url_with_subpath(self):
        result = to_nitter_rss("https://twitter.com/user/status/123", NITTER_INSTANCE)
        assert result == "https://nitter.net/user/rss"

    def test_custom_instance(self):
        result = to_nitter_rss("@user", "https://my-nitter.example.org")
        assert result == "https://my-nitter.example.org/user/rss"

    def test_empty_path_raises(self):
        with pytest.raises(ValueError, match="Cannot extract username"):
            to_nitter_rss("https://twitter.com/", NITTER_INSTANCE)
