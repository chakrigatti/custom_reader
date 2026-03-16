% READER-FETCH(1) Reader CLI | Reader CLI Manual

# NAME

reader-fetch — fetch new articles from feeds

# SYNOPSIS

**reader fetch** [*feed_id*]

# DESCRIPTION

Fetches and stores new articles from subscribed feeds. Deduplicates by URL so
re-fetching a feed never creates duplicate articles.

If *feed_id* is given, only that feed is fetched. If omitted, all feeds are
fetched in sequence.

Feeds with source_type **bookmark** are silently skipped in both modes —
bookmark articles are created manually via **reader-save**(1), not fetched
automatically.

After fetching, prints the number of new articles retrieved for each feed.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Fetch completed (even if 0 new articles were found).

**1**
: Feed not found (404), fetch network/HTTP failure (422), or server error.

# EXAMPLES

Fetch all feeds:

    reader fetch

Fetch a single feed by ID:

    reader fetch 2

Example output (all feeds):

    Fetched 5 new articles from "Example Blog"
    Fetched 0 new articles from "@username"

# SEE ALSO

**reader**(1), **reader-add**(1), **reader-articles**(1)
