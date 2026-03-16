% READER-ADD(1) Reader CLI | Reader CLI Manual

# NAME

reader-add — add a feed to the reader

# SYNOPSIS

**reader add** *url*

# DESCRIPTION

Adds a new feed identified by *url*. The server auto-detects the source type:

- **RSS/Atom:** If the URL points directly to an RSS or Atom feed it is used as-is.
- **Blog:** If the URL is a blog homepage the server crawls it for a
  `<link rel="alternate">` tag and common feed paths (`/feed`, `/rss`,
  `/atom.xml`, `/feed.xml`, `/index.xml`).
- **Nitter/X:** An X/Twitter handle (e.g. `@user`) or nitter URL is converted
  to a nitter RSS URL using the configured nitter instance.

Returns an error if the URL cannot be resolved to a valid feed.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Feed added successfully.

**1**
: Feed already exists (409), URL could not be resolved to a feed (422), or
  network/server error.

# EXAMPLES

Add an RSS feed directly:

    reader add https://example.com/feed.xml

Add a blog homepage (feed auto-discovered):

    reader add https://example.com

Add an X/Twitter account via handle:

    reader add @username

Add a nitter URL:

    reader add https://nitter.example.com/username

# SEE ALSO

**reader**(1), **reader-feeds**(1), **reader-fetch**(1)
