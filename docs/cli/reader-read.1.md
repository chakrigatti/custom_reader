% READER-READ(1) Reader CLI | Reader CLI Manual

# NAME

reader-read — render an article as markdown in the terminal

# SYNOPSIS

**reader read** *article_id*

# DESCRIPTION

Fetches the article identified by *article_id* and renders its markdown content
in the terminal using **rich**. After rendering, the article state is
automatically set to **read** (via **PATCH /articles/{id}**) unless it was
already marked **read_again**.

Use **reader-articles**(1) to find article IDs.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Article rendered successfully.

**1**
: Article not found (404) or network/server error.

# EXAMPLES

Read article 42:

    reader read 42

# SEE ALSO

**reader**(1), **reader-articles**(1), **reader-mark**(1)
