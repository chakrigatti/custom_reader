from __future__ import annotations

import pytest
import respx
from httpx import Response

from reader.services.favicon import fetch_favicon_url


@pytest.mark.asyncio
@respx.mock
async def test_favicon_ico_found():
    respx.head("https://example.com/favicon.ico").mock(
        return_value=Response(200, headers={"content-type": "image/x-icon"})
    )
    result = await fetch_favicon_url("https://example.com")
    assert result == "https://example.com/favicon.ico"


@pytest.mark.asyncio
@respx.mock
async def test_favicon_from_link_tag():
    respx.head("https://example.com/favicon.ico").mock(
        return_value=Response(404)
    )
    respx.get("https://example.com").mock(
        return_value=Response(
            200,
            text='<html><head><link rel="icon" href="/img/icon.png"></head></html>',
        )
    )
    result = await fetch_favicon_url("https://example.com")
    assert result == "https://example.com/img/icon.png"


@pytest.mark.asyncio
@respx.mock
async def test_favicon_not_found():
    respx.head("https://example.com/favicon.ico").mock(
        return_value=Response(404)
    )
    respx.get("https://example.com").mock(
        return_value=Response(200, text="<html><head></head></html>")
    )
    result = await fetch_favicon_url("https://example.com")
    assert result is None
