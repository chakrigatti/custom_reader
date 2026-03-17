from __future__ import annotations

import sys
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from reader.config import settings

console = Console()


def get_client() -> httpx.Client:
    return httpx.Client(base_url=settings.server_url, timeout=30.0)


def handle_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        try:
            body = response.json()
            detail = body.get("detail", response.text)
        except Exception:
            detail = response.text
        console.print("[red]Error ({}):[/red] {}".format(response.status_code, detail))
        sys.exit(1)


@click.group()
def cli():
    """Reader - A personal RSS feed reader."""
    pass


@cli.command()
@click.argument("url")
def add(url: str):
    """Add a feed by URL (auto-detects RSS, blog, or X/nitter)."""
    with get_client() as client:
        response = client.post("/feeds", json={"url": url})
        handle_error(response)
        feed = response.json()
        console.print("Added feed #{}: {}".format(feed["id"], feed["title"]))


@cli.command()
def feeds():
    """List all subscribed feeds."""
    with get_client() as client:
        response = client.get("/feeds")
        handle_error(response)
        data = response.json()

        table = Table(title="Feeds")
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("Type", style="green")
        table.add_column("URL")
        table.add_column("Last Fetched")

        for feed in data["data"]:
            table.add_row(
                str(feed["id"]),
                feed["title"],
                feed["source_type"],
                feed["feed_url"],
                feed.get("last_fetched_at") or "Never",
            )
        console.print(table)


@cli.command()
@click.argument("feed_id", type=int)
def remove(feed_id: int):
    """Delete a feed by ID."""
    with get_client() as client:
        response = client.delete("/feeds/{}".format(feed_id))
        handle_error(response)
        console.print("Removed feed #{}".format(feed_id))


@cli.command()
@click.argument("feed_id", type=int, required=False)
def fetch(feed_id: Optional[int]):
    """Fetch new articles. Optionally specify a feed ID."""
    with get_client() as client:
        if feed_id:
            response = client.post("/feeds/{}/sync".format(feed_id))
            handle_error(response)
            result = response.json()
            console.print(
                "Fetched {} new articles from {}".format(
                    result["fetched"], result["title"]
                )
            )
        else:
            response = client.post("/sync")
            handle_error(response)
            data = response.json()
            for result in data["data"]:
                console.print(
                    "  {}: {} new articles".format(
                        result["title"], result["fetched"]
                    )
                )
            console.print("Total: {} feeds synced".format(data["total"]))


@cli.command()
@click.argument("url")
def save(url: str):
    """Save a URL as a bookmark article."""
    with get_client() as client:
        response = client.post("/articles", json={"url": url})
        handle_error(response)
        article = response.json()
        msg = "Saved article #{}: {}".format(article["id"], article["title"])
        if article.get("warning"):
            msg += "\n[yellow]Warning:[/yellow] {}".format(article["warning"])
        console.print(msg)


@cli.command()
@click.option("--feed", "feed_id", type=int, help="Filter by feed ID")
@click.option("--state", type=click.Choice(["unread", "read", "read_again"]))
@click.option("--saved", is_flag=True, help="Show only bookmarked articles")
@click.option("--tag", type=str, help="Filter by tag name")
def articles(feed_id: Optional[int], state: Optional[str], saved: bool, tag: Optional[str]):
    """List articles with optional filters."""
    with get_client() as client:
        params = {}
        if feed_id:
            params["feed_id"] = feed_id
        if state:
            params["state"] = state
        if saved:
            params["source"] = "bookmark"
        if tag:
            params["tag"] = tag

        response = client.get("/articles", params=params)
        handle_error(response)
        data = response.json()

        table = Table(title="Articles")
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("State", style="green")
        table.add_column("Published")

        for article in data["data"]:
            table.add_row(
                str(article["id"]),
                article["title"][:60],
                article["state"],
                article.get("published_at") or "",
            )
        console.print(table)
        console.print(
            "Showing {} of {} articles".format(len(data["data"]), data["total"])
        )


@cli.command()
@click.argument("article_id", type=int)
def read(article_id: int):
    """Read an article rendered as markdown in the terminal."""
    with get_client() as client:
        response = client.get(
            "/articles/{}".format(article_id),
            headers={"Accept": "text/markdown"},
        )
        handle_error(response)
        console.print(Markdown(response.text))

        # Mark as read
        client.patch(
            "/articles/{}".format(article_id), json={"state": "read"}
        )


@cli.command()
@click.argument("article_id", type=int)
@click.argument("state", type=click.Choice(["unread", "read", "read_again"]))
def mark(article_id: int, state: str):
    """Set an article's read state."""
    with get_client() as client:
        response = client.patch(
            "/articles/{}".format(article_id), json={"state": state}
        )
        handle_error(response)
        console.print("Marked article #{} as {}".format(article_id, state))


@cli.command()
def categories():
    """List all categories."""
    with get_client() as client:
        response = client.get("/categories")
        handle_error(response)
        data = response.json()

        table = Table(title="Categories")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Created")

        for cat in data["data"]:
            table.add_row(
                str(cat["id"]),
                cat["name"],
                cat.get("created_at", ""),
            )
        console.print(table)


@cli.command()
@click.argument("feed_id", type=int)
@click.argument("category", type=str)
def categorize(feed_id: int, category: str):
    """Assign a feed to a category."""
    with get_client() as client:
        # Get current feed categories
        response = client.get("/feeds/{}".format(feed_id))
        handle_error(response)
        feed = response.json()
        existing_ids = [c["id"] for c in feed.get("categories", [])]

        # Create or find category
        cat_response = client.get("/categories")
        handle_error(cat_response)
        cats = cat_response.json()["data"]
        cat_id = None
        for c in cats:
            if c["name"] == category:
                cat_id = c["id"]
                break

        if cat_id is None:
            create_resp = client.post("/categories", json={"name": category})
            handle_error(create_resp)
            cat_id = create_resp.json()["id"]

        if cat_id not in existing_ids:
            existing_ids.append(cat_id)

        response = client.put(
            "/feeds/{}/categories".format(feed_id),
            json={"category_ids": existing_ids},
        )
        handle_error(response)
        console.print(
            "Feed #{} categorized as '{}'".format(feed_id, category)
        )


@cli.command(name="tag")
@click.argument("article_id", type=int)
@click.argument("tag_name", type=str)
def tag_article(article_id: int, tag_name: str):
    """Tag an article."""
    with get_client() as client:
        response = client.post(
            "/articles/{}/tags".format(article_id),
            json={"name": tag_name},
        )
        handle_error(response)
        console.print(
            "Tagged article #{} with '{}'".format(article_id, tag_name)
        )


@cli.command(name="import")
@click.argument("file", type=click.Path(exists=True))
def import_opml(file: str):
    """Import feeds from an OPML file."""
    with open(file, "rb") as f:
        content = f.read()

    with get_client() as client:
        response = client.post(
            "/opml/import",
            files={"file": ("feeds.opml", content, "application/xml")},
        )
        handle_error(response)
        result = response.json()
        console.print(
            "Imported: {}, Skipped: {}, Errors: {}".format(
                result["imported"], result["skipped"], len(result["errors"])
            )
        )
        for err in result["errors"]:
            console.print("[yellow]  {}[/yellow]".format(err))


@cli.command(name="export")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def export_opml(output: Optional[str]):
    """Export feeds as OPML."""
    with get_client() as client:
        response = client.get("/opml/export")
        handle_error(response)

        if output:
            with open(output, "w") as f:
                f.write(response.text)
            console.print("Exported to {}".format(output))
        else:
            console.print(response.text)
