"""Generate the dashboard favicon and inline it into dashboard.html.

    python3 make_favicon.py

Writes favicon.svg and rewrites the <link rel="icon"> data URI in dashboard.html. The icon is
inlined rather than served: dashboard.py whitelists its routes, so a /favicon.ico request would
404, and a data URI needs no request at all.

Two shapes: a leaf on a tile, in the project's aqua. An earlier version drew a rising chart curve,
which was wrong twice over -- it read as a generic analytics app, and a *rising* line reads as
"growth, going well", which is the opposite of what a cost meter should say.

Sized for 16 px rather than for the 128 px preview, because 16 px is the size that actually appears
in a tab. That is also why nothing was added inside the leaf: variants with a vein-as-chart-line or
bar-chart veins both read at 48 px and turned to noise at 16.

Colours are the project palette used everywhere else: aqua #1baf7a, surface #fcfcfb.

make_app.py imports svg() from here for the macOS app icon, which is the same mark inset inside
the canvas rather than a second drawing of it.
"""
import pathlib
import re
import urllib.parse

AQUA, SURFACE = "#1baf7a", "#fcfcfb"

# One closed path: two symmetric quadratic-ish arcs meeting at the tip and the tail, on the
# diagonal. Symmetry about the diagonal is what makes it survive being 16 px across.
LEAF = "M25.5 6.5 C25.5 17 17 25.5 6.5 25.5 C6.5 15 15 6.5 25.5 6.5 Z"

MARK = (
    f'<rect width="32" height="32" rx="7" fill="{AQUA}"/>'
    f'<path d="{LEAF}" fill="{SURFACE}"/>'
)


def svg(pad=0.0):
    """The mark on a 32-unit canvas, inset by `pad` on every side.

    pad=0 fills the canvas, which is what a favicon wants. The app icon uses a pad because macOS
    expects the artwork to sit on about 80% of the icon grid with transparent margin -- a
    full-bleed tile reads as oversized next to every other icon in the Dock."""
    if not pad:
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{MARK}</svg>'
    scale = (32 - 2 * pad) / 32
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            f'<g transform="translate({pad:g},{pad:g}) scale({scale:g})">{MARK}</g></svg>')


if __name__ == "__main__":
    icon = svg()
    pathlib.Path("favicon.svg").write_text(icon + "\n")
    uri = "data:image/svg+xml," + urllib.parse.quote(icon, safe="")

    html = pathlib.Path("dashboard.html")
    s = html.read_text()
    s, n = re.subn(r'<link rel="icon" href="[^"]*">', f'<link rel="icon" href="{uri}">', s, count=1)
    if not n:
        raise SystemExit("no <link rel=\"icon\"> found in dashboard.html — add one first")
    html.write_text(s)
    print(f"favicon.svg written; data URI is {len(uri)} chars, inlined into dashboard.html")
