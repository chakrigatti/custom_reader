% READER(1) Reader CLI | Reader CLI Manual

# NAME

reader — personal RSS reader command-line interface

# SYNOPSIS

**reader** \<command\> [*options*] [*arguments*]

# DESCRIPTION

**reader** is a command-line RSS reader that aggregates articles from RSS/Atom
feeds, blog URLs, and X/Twitter accounts via Nitter. It stores articles locally
in SQLite and renders them as markdown in the terminal.

The CLI is a thin HTTP client. All reads and writes go through a local FastAPI
server (default: `http://localhost:8000`). The server must be running before
using any command.

# COMMANDS

**add** *url*
: Add a feed. Auto-detects source type (RSS, blog, nitter/X). See **reader-add**(1).

**feeds**
: List all subscribed feeds. See **reader-feeds**(1).

**remove** *feed_id*
: Remove a feed by ID. See **reader-remove**(1).

**fetch** [*feed_id*]
: Fetch new articles (all feeds if no ID given). See **reader-fetch**(1).

**save** *url*
: Save a standalone URL as a bookmark article. See **reader-save**(1).

**articles** [--feed *id*] [--state *state*] [--saved]
: List articles with optional filters. See **reader-articles**(1).

**read** *article_id*
: Render an article as markdown in the terminal. See **reader-read**(1).

**mark** *article_id* *state*
: Set an article's reading state. See **reader-mark**(1).

**categories**
: List all categories. See **reader-categories**(1).

**categorize** *feed_id* *category*
: Assign a feed to a category. See **reader-categorize**(1).

**tag** *article_id* *tag_name*
: Tag an article. See **reader-tag**(1).

**import** *file*
: Import feeds from an OPML file. See **reader-import**(1).

**export** [--output *file*]
: Export feeds as OPML. See **reader-export**(1).

# OPTIONS

**--help**
: Show help message and exit. Available on **reader** and every subcommand.

# EXIT STATUS

**0**
: Success.

**1**
: An error occurred (API error, network failure, invalid input).

# EXAMPLES

Start the API server, then run commands:

    uvicorn reader.server:app --reload &
    reader add https://example.com/feed.xml
    reader fetch
    reader articles --state unread
    reader read 42

# SEE ALSO

**reader-add**(1), **reader-feeds**(1), **reader-remove**(1),
**reader-fetch**(1), **reader-save**(1), **reader-articles**(1),
**reader-read**(1), **reader-mark**(1), **reader-categories**(1),
**reader-categorize**(1), **reader-tag**(1), **reader-import**(1),
**reader-export**(1)
