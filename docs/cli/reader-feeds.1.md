% READER-FEEDS(1) Reader CLI | Reader CLI Manual

# NAME

reader-feeds — list all subscribed feeds

# SYNOPSIS

**reader feeds**

# DESCRIPTION

Prints a table of all subscribed feeds. Output columns:

| Column | Description |
|--------|-------------|
| id | Feed ID (used with **reader-remove**(1) and **reader-fetch**(1)) |
| title | Feed title |
| source_type | One of: rss, blog, nitter, bookmark |
| last_fetched_at | Timestamp of the last successful fetch, or blank if never fetched |

The sentinel "Saved Articles" feed (id=1, source_type=bookmark) is always
present and is always listed.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Success (even if no feeds are subscribed).

**1**
: Network or server error.

# EXAMPLES

    reader feeds

Example output:

    id  title               source_type  last_fetched_at
    1   Saved Articles      bookmark
    2   Example Blog        rss          2026-03-15 08:00
    3   @username           nitter       2026-03-15 08:01

# SEE ALSO

**reader**(1), **reader-add**(1), **reader-remove**(1)
