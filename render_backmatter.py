"""
render_backmatter.py
─────────────────────────────────────────────────────────────────────────────
Compact solutions section: for each puzzle, prints the fully resolved
row-by-row answer (Person - attribute1 - attribute2 - ordinal), grouped
several puzzles per page rather than a full solved grid per puzzle (100
more full-page grids would double the book length for no real benefit --
solvers checking their answer just need the resolved pairings).
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors

PAGE_W, PAGE_H = 8.5 * IN, 11 * IN
MARGIN = 0.75 * IN
COL_GAP = 0.35 * IN
N_COLS = 2


def _solution_rows(puzzle: dict):
    """Rebuild the resolved row-by-row answer from categories + solution.
    Uses the known puzzle structure (person category first, ordinal category
    last -- true for every theme in themes.py) rather than trying to detect
    the anchor from solution data, since more than one category's random
    permutation can coincidentally look like an identity mapping."""
    cats = puzzle["categories"]
    names = list(cats.keys())
    sol = puzzle["solution"]
    N = len(next(iter(cats.values())))

    person_name = names[0]
    ordinal_name = names[-1]
    attr_names = names[1:-1]
    display_order = [person_name] + attr_names + [ordinal_name]

    rows = []
    for i in range(N):  # i = index into the ordinal category = value (i+1)
        slot = sol[ordinal_name][i]
        parts = []
        for name in display_order:
            item_idx = sol[name].index(slot)
            parts.append(_clean(cats[name][item_idx]))
        rows.append(" - ".join(parts))
    return rows


import re


def _clean(s: str) -> str:
    s = re.sub(r"^(a|an|the)\s+", "", s.strip(), flags=re.IGNORECASE)
    words = s.split(" ")
    out = []
    for w in words:
        parts = w.split("-")
        out.append("-".join(p[:1].upper() + p[1:] if p else p for p in parts))
    return " ".join(out)


def draw_solutions_pages(c, puzzles: list, puzzles_per_page: int = 6):
    w = PAGE_W - 2 * MARGIN
    col_w = (w - COL_GAP) / N_COLS

    i = 0
    first_page = True
    while i < len(puzzles):
        if not first_page:
            c.showPage()
        first_page = False
        c.setFont("Helvetica-Bold", 16)
        c.drawString(MARGIN, PAGE_H - MARGIN - 5, "Solutions")
        y_top = PAGE_H - MARGIN - 40

        batch = puzzles[i:i + puzzles_per_page]
        per_col = (len(batch) + N_COLS - 1) // N_COLS
        for j, p in enumerate(batch):
            col = j // per_col
            row_in_col = j % per_col
            x = MARGIN + col * (col_w + COL_GAP)
            y = y_top - row_in_col * ((PAGE_H - 2 * MARGIN - 40) / max(per_col, 1))

            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, y, f"Puzzle {p['puzzle_index']}  {p['title']}")
            y -= 13
            c.setFont("Helvetica", 8.5)
            for line in _solution_rows(p):
                c.drawString(x + 4, y, line)
                y -= 11
        i += puzzles_per_page
