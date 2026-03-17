% READER-EXPORT(1) Reader CLI | Reader CLI Manual

# NAME

reader-export — export feeds as OPML

# SYNOPSIS

**reader export** [**--output** *file*]

# DESCRIPTION

Exports all subscribed feeds as an OPML 2.0 XML document. Feeds with
categories are nested under folder outlines. Without **--output**, the XML
is printed to stdout.

# OPTIONS

**--output** *file*, **-o** *file*
: Write the OPML to *file* instead of stdout.

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Export completed.

**1**
: API error or network/server error.

# EXAMPLES

    reader export -o feeds.opml
    reader export > backup.opml

# SEE ALSO

**reader**(1), **reader-import**(1), **reader-feeds**(1)
