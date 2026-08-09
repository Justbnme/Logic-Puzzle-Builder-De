"""
fonts.py
─────────────────────────────────────────────────────────────────────────────
Registers real, embeddable TTF fonts for use across all renderers.

ReportLab's built-in "Helvetica" / "Helvetica-Bold" / "Helvetica-Oblique"
names refer to the 14 standard PDF fonts, which ReportLab does NOT embed --
it just references them by name and assumes the reader's PDF viewer has
them. KDP requires every font to be embedded regardless, so PDFs built with
the bare Helvetica names get flagged during upload.

Liberation Sans is a metrically-compatible, open-license clone of Arial/
Helvetica (pre-installed on this system), so swapping to it changes
essentially nothing visually while producing a properly embedded PDF.

Import this module before any Canvas drawing happens; every other renderer
imports FONT_REGULAR / FONT_BOLD / FONT_ITALIC / FONT_BOLDITALIC from here
instead of hardcoding "Helvetica" strings.
"""

import glob
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/",
    "/usr/share/fonts/liberation/",
]

_dir = None
for d in _CANDIDATES:
    if glob.glob(d + "LiberationSans-Regular.ttf"):
        _dir = d
        break
if _dir is None:
    found = glob.glob("/usr/share/fonts/**/LiberationSans-Regular.ttf", recursive=True)
    if not found:
        raise RuntimeError("LiberationSans TTF files not found -- install fonts-liberation")
    _dir = found[0].rsplit("/", 1)[0] + "/"

FONT_REGULAR = "LiberationSans"
FONT_BOLD = "LiberationSans-Bold"
FONT_ITALIC = "LiberationSans-Italic"
FONT_BOLDITALIC = "LiberationSans-BoldItalic"

pdfmetrics.registerFont(TTFont(FONT_REGULAR, _dir + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, _dir + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont(FONT_ITALIC, _dir + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLDITALIC, _dir + "LiberationSans-BoldItalic.ttf"))

# ReportLab's Canvas hardcodes "Helvetica" as its internal default text
# state on every page, regardless of what font is explicitly set -- this
# leaves a dangling unembedded font reference on EVERY page even if never
# used to draw a visible glyph, which is exactly what KDP's checker flags.
# Overriding the standard names directly (not just adding new ones) makes
# that internal default resolve to the embedded font too, and also
# safety-nets against any stray "Helvetica" string missed elsewhere.
pdfmetrics.registerFont(TTFont("Helvetica", _dir + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Helvetica-Bold", _dir + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Helvetica-Oblique", _dir + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Helvetica-BoldOblique", _dir + "LiberationSans-BoldItalic.ttf"))
