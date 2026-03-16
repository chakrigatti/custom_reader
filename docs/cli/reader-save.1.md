% READER-SAVE(1) Reader CLI | Reader CLI Manual

# NAME

reader-save — save a standalone URL as a bookmark article

# SYNOPSIS

**reader save** *url*

# DESCRIPTION

Fetches the page at *url*, extracts the main content, and saves it as a
bookmark article under the "Saved Articles" feed (id=1).

The *url* must use the **http** or **https** scheme. Other schemes (ftp, file,
etc.) are rejected before the request is sent.

**Processing:**

1. Validate URL scheme → error + exit 1 if not http/https.
2. Check for duplicate: if the URL was already saved, print
   `Already saved as article #<id>` and exit 0.
3. Fetch the page (15 s timeout, follows redirects) → error + exit 1 on failure.
4. Extract content via trafilatura; convert to markdown via markdownify.
5. Generate summary from first 300 characters of plain text.
6. Save and print confirmation.

If no content can be extracted the article is still saved; a warning is printed.

# OPTIONS

**--help**
: Show help message and exit.

# EXIT STATUS

**0**
: Article saved (201) or already existed (409).

**1**
: Invalid URL scheme, network failure, HTTP error fetching the page (422), or
  server error.

# EXAMPLES

Save an article:

    reader save https://example.com/article

Output on success (201):

    Saved article #7: Example Article Title

Output when already saved (409):

    Already saved as article #7

Output on extraction failure (201 with warning):

    Saved article #8: https://example.com/article
    Warning: no content could be extracted from this page

# SEE ALSO

**reader**(1), **reader-articles**(1), **reader-read**(1)
