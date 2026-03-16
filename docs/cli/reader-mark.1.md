% READER-MARK(1) Reader CLI | Reader CLI Manual

# NAME

reader-mark — set an article's reading state

# SYNOPSIS

**reader mark** *article_id* *state*

# DESCRIPTION

Updates the reading state of the article identified by *article_id* to *state*.

Valid values for *state*:

**unread**
: Mark the article as not yet read (default state for new articles).

**read**
: Mark the article as read. **reader-read**(1) sets this automatically after
  rendering.

**read_again**
: Flag the article to be read again. **reader-read**(1) will not auto-mark
  this state to **read**, preserving the flag.

Use **reader-articles**(1) to find article IDs.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: State updated successfully.

**1**
: Article not found (404), invalid state value (422), or network/server error.

# EXAMPLES

Mark article 42 as read:

    reader mark 42 read

Flag article 42 to read again later:

    reader mark 42 read_again

Reset article 42 to unread:

    reader mark 42 unread

# SEE ALSO

**reader**(1), **reader-articles**(1), **reader-read**(1)
