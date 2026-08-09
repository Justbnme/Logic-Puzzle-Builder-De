"""
render_page.py
─────────────────────────────────────────────────────────────────────────────
Renders one complete Master Logic puzzle page: title, difficulty badge,
intro flavor text, the logic grid, and a two-column numbered clue list --
all on a single 8.5x11 page (no two-page spread), matching the established
single-page format from Logic Plain & Simple.
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from grid import draw_logic_grid

PAGE_W, PAGE_H = 8.5 * IN, 11 * IN
MARGIN = 0.625 * IN


def draw_puzzle_page(c: canvas.Canvas, puzzle: dict, puzzle_num_in_book: int):
    ox = MARGIN
    oy = PAGE_H - MARGIN

    # -- title row + difficulty badge --
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(colors.black)
    c.drawString(ox, oy - 15, f"Puzzle {puzzle_num_in_book}   {puzzle['title']}")

    badge = puzzle["difficulty"].upper()
    c.setFont("Helvetica-Bold", 8.5)
    bw = c.stringWidth(badge, "Helvetica-Bold", 8.5) + 14
    bx = PAGE_W - MARGIN - bw
    c.setFillColor(colors.black)
    c.roundRect(bx, oy - 16, bw, 15, 3, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawCentredString(bx + bw / 2, oy - 12, badge)

    # -- intro flavor text --
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Oblique", 8.5)
    intro_y = oy - 34
    intro_lines = _wrap(c, puzzle["intro"], "Helvetica-Oblique", 8.5, PAGE_W - 2 * MARGIN)
    for line in intro_lines:
        c.drawString(ox, intro_y, line)
        intro_y -= 11

    # -- grid --
    grid_top = intro_y - 10
    gw, gh_bottom = draw_logic_grid(c, ox, grid_top, puzzle["categories"], trim="8.5x11")

    # -- clue list, two columns --
    clues = puzzle["clues"]
    clue_top = gh_bottom - 14
    col_w = (PAGE_W - 2 * MARGIN - 0.25 * IN) / 2
    half = (len(clues) + 1) // 2
    col1, col2 = clues[:half], clues[half:]

    c.setFont("Helvetica-Bold", 9)
    c.drawString(ox, clue_top, "Clues")
    clue_top -= 13

    for col_idx, col in enumerate((col1, col2)):
        cx = ox + col_idx * (col_w + 0.25 * IN)
        cy = clue_top
        for i, clue_text in enumerate(col):
            n = i + 1 if col_idx == 0 else half + i + 1
            lines = _wrap(c, f"{n}. {clue_text}", "Helvetica", 8, col_w)
            c.setFont("Helvetica", 8)
            for li, line in enumerate(lines):
                c.drawString(cx, cy, line)
                cy -= 10.5
            cy -= 1.5


def _wrap(c, text, font, size, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if c.stringWidth(trial, font, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
