% READER-TAG(1) Reader CLI | Reader CLI Manual

# NAME

reader-tag — tag an article

# SYNOPSIS

**reader tag** *article_id* *tag_name*

# DESCRIPTION

Adds the named *tag_name* to the article identified by *article_id*. If the
tag does not exist, it is created automatically. An article can have multiple
tags.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Article tagged successfully.

**1**
: Article not found (404), or network/server error.

# EXAMPLES

    reader tag 42 python
    reader tag 42 "machine-learning"

# SEE ALSO

**reader**(1), **reader-articles**(1)
