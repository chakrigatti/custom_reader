% READER-ARTICLES(1) Reader CLI | Reader CLI Manual

# NAME

reader-articles — list articles with optional filters

# SYNOPSIS

**reader articles** [**--feed** *id*] [**--state** *state*] [**--saved**]

# DESCRIPTION

Prints a table of articles. Without options, all articles are listed. Filters
can be combined (except where noted).

The "Feed" column displays the feed title, or **Saved** for bookmark articles
that belong to the "Saved Articles" feed.

# OPTIONS

**--feed** *id*
: Filter to articles from the feed with the given ID. Mutually exclusive with
  **--saved**.

**--state** *state*
: Filter by reading state. Valid values: **unread**, **read**, **read_again**.

**--saved**
: Filter to bookmark articles only (articles saved with **reader-save**(1)).
  Mutually exclusive with **--feed**.

**--tag** *name*
: Filter to articles with the given tag.

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Success (even if no articles match).

**1**
: Invalid option combination, API error, or network/server error.

# EXAMPLES

List all unread articles:

    reader articles --state unread

List articles from feed 2:

    reader articles --feed 2

List all saved bookmarks:

    reader articles --saved

List unread bookmarks:

    reader articles --saved --state unread

Example output:

    id   Feed           state    title
    42   Example Blog   unread   How to do the thing
    43   Saved          unread   Interesting article I saved

# SEE ALSO

**reader**(1), **reader-fetch**(1), **reader-read**(1), **reader-mark**(1),
**reader-save**(1)
