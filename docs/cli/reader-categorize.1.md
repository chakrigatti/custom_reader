% READER-CATEGORIZE(1) Reader CLI | Reader CLI Manual

# NAME

reader-categorize — assign a feed to a category

# SYNOPSIS

**reader categorize** *feed_id* *category*

# DESCRIPTION

Assigns the feed identified by *feed_id* to the named *category*. If the
category does not exist, it is created automatically. A feed can belong to
multiple categories; run the command multiple times with different category
names.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Feed categorized successfully.

**1**
: Feed not found (404), or network/server error.

# EXAMPLES

    reader categorize 3 Technology
    reader categorize 3 "Daily Reading"

# SEE ALSO

**reader**(1), **reader-categories**(1), **reader-feeds**(1)
