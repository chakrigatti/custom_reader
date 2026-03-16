"""Simple HTTP server that renders man page Markdowns to HTML."""
import http.server
import pathlib
import re
import urllib.parse
import mistune

ROOT = pathlib.Path(__file__).parent
PAGES = sorted(ROOT.glob("*.1.md"))

MD = mistune.create_markdown(escape=False)

CSS = """
body { font-family: monospace; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #222; }
h1 { border-bottom: 2px solid #444; padding-bottom: .3rem; }
h2 { border-bottom: 1px solid #aaa; }
nav { margin-bottom: 1.5rem; }
nav a { margin-right: 1rem; text-decoration: none; color: #0066cc; }
nav a:hover { text-decoration: underline; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: .4rem .7rem; text-align: left; }
th { background: #f4f4f4; }
code { background: #f4f4f4; padding: .1rem .3rem; border-radius: 3px; }
pre code { background: none; padding: 0; }
pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; }
"""

def nav_links():
    links = '<nav>'
    for p in PAGES:
        name = p.stem  # e.g. reader-add.1
        href = f"/{urllib.parse.quote(p.name)}"
        links += f'<a href="{href}">{name}</a>'
    links += '</nav>'
    return links

def render_page(path: pathlib.Path) -> str:
    src = path.read_text()
    # strip pandoc title block (% lines at top)
    src = re.sub(r'^%[^\n]*\n', '', src, flags=re.MULTILINE)
    body = MD(src)
    title = path.stem
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title}</title>
<style>{CSS}</style></head>
<body>
{nav_links()}
{body}
</body></html>"""

def index_page() -> str:
    items = "".join(
        f'<li><a href="/{urllib.parse.quote(p.name)}">{p.stem}</a></li>'
        for p in PAGES
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Reader CLI Man Pages</title>
<style>{CSS}</style></head>
<body>
<h1>Reader CLI Man Pages</h1>
<ul>{items}</ul>
</body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def send_html(self, html: str, status: int = 200):
        encoded = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urllib.parse.unquote(self.path.lstrip("/"))
        if not path or path == "index.html":
            self.send_html(index_page())
            return
        target = ROOT / path
        if target in PAGES:
            self.send_html(render_page(target))
        else:
            self.send_html("<h1>404 Not Found</h1>", 404)

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    server = http.server.HTTPServer(("", port), Handler)
    print(f"Man pages server running at http://localhost:{port}")
    server.serve_forever()
