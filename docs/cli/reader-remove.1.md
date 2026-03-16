% READER-REMOVE(1) Reader CLI | Reader CLI Manual

# NAME

reader-remove — remove a subscribed feed

# SYNOPSIS

**reader remove** *feed_id*

# DESCRIPTION

Removes the feed identified by *feed_id* and all its associated articles from
the local database.

**Note:** The sentinel "Saved Articles" feed (id=1) cannot be removed. Attempting
to do so returns a 403 error and exits with status 1. This feed is the parent of
all bookmark articles saved with **reader-save**(1).

Use **reader-feeds**(1) to look up feed IDs.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Feed removed successfully.

**1**
: Feed not found (404), feed is the protected sentinel (403), or
  network/server error.

# EXAMPLES

Remove feed with ID 3:

    reader remove 3

Attempting to remove the sentinel feed:

    reader remove 1
    # Error: feed id=1 (Saved Articles) cannot be removed

# SEE ALSO

**reader**(1), **reader-feeds**(1), **reader-add**(1)
