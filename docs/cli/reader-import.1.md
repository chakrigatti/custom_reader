% READER-IMPORT(1) Reader CLI | Reader CLI Manual

# NAME

reader-import — import feeds from an OPML file

# SYNOPSIS

**reader import** *file*

# DESCRIPTION

Reads the OPML file at *file* and bulk-creates feeds. OPML folder
elements are mapped to categories. Feeds that already exist are skipped.
A summary of imported, skipped, and errored feeds is printed.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Import completed (some feeds may have been skipped or errored).

**1**
: File not found, invalid OPML, or network/server error.

# EXAMPLES

    reader import subscriptions.opml
    reader import ~/Downloads/feedly-export.opml

# SEE ALSO

**reader**(1), **reader-export**(1), **reader-feeds**(1)
