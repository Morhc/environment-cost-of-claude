"""Generate the dashboard favicon and inline it into dashboard.html.

    python3 make_favicon.py

Writes favicon.svg and rewrites the <link rel="icon"> data URI in dashboard.html. The icon is
inlined rather than served: dashboard.py whitelists its routes, so a /favicon.ico request would
404, and a data URI needs no request at all.

Three shapes only, and sized for 16 px rather than for the 128 px preview: the stroke is heavier
and the dot pulled in from the corner than a large-only design would want, because 16 px is the
size that actually appears in a tab.
Colours are the project palette used everywhere else: blue #2a78d6, orange #eb6834, surface
#fcfcfb. The mark is the dashboard's own chart shrunk down — a cumulative curve rising to a point.
"""
import pathlib
import re
import urllib.parse

BLUE, ORANGE, SURFACE = "#2a78d6", "#eb6834", "#fcfcfb"

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    f'<rect width="32" height="32" rx="7" fill="{BLUE}"/>'
    '<path d="M6.5 25 C13 24.5 16 20 20 13.5 C21.8 10.6 23.2 9.2 25 8.2" '
    f'fill="none" stroke="{SURFACE}" stroke-width="4.2" stroke-linecap="round"/>'
    f'<circle cx="25" cy="8.2" r="4" fill="{ORANGE}" stroke="{BLUE}" stroke-width="1.1"/>'
    '</svg>'
)

pathlib.Path("favicon.svg").write_text(SVG + "\n")
uri = "data:image/svg+xml," + urllib.parse.quote(SVG, safe="")

html = pathlib.Path("dashboard.html")
s = html.read_text()
s, n = re.subn(r'<link rel="icon" href="[^"]*">', f'<link rel="icon" href="{uri}">', s, count=1)
if not n:
    raise SystemExit("no <link rel=\"icon\"> found in dashboard.html — add one first")
html.write_text(s)
print(f"favicon.svg written; data URI is {len(uri)} chars, inlined into dashboard.html")
