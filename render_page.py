"""
render_page.py
─────────────────────────────────────────────────────────────────────────────
Renders one Master Logic puzzle as a TWO-PAGE spread: grid page (title,
difficulty badge, intro, grid) followed by a clues page (full clue list).

A single combined page was tried first, but the grid alone needs ~550pt of
a ~700pt usable page height to keep 21 columns readable, leaving too little
room for puzzles with many/long clues (10-19 range) -- no font size, however
small, can make that fit for the worst cases. Splitting across two pages
gives the clue list a nearly full page, which comfortably fits every
puzzle in the book without ever needing to shrink below a readable size.
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from grid import draw_logic_grid
import fonts as _fonts

FONT = _fonts.FONT_REGULAR
FONT_B = _fonts.FONT_BOLD
FONT_I = _fonts.FONT_ITALIC

PAGE_W, PAGE_H = 8.5 * IN, 11 * IN
MARGIN = 0.625 * IN

CLUE_FONT_MAX = 11.0
CLUE_FONT_MIN = 8.0


def _draw_header(c, puzzle, puzzle_num_in_book, suffix=""):
    oy = PAGE_H - MARGIN
    c.setFont(FONT_B, 15)
    c.setFillColor(colors.black)
    title = f"Puzzle {puzzle_num_in_book}   {puzzle['title']}"
    if suffix:
        title += f"   {suffix}"
    c.drawString(MARGIN, oy - 15, title)

    badge = puzzle["difficulty"].upper()
    c.setFont(FONT_B, 8.5)
    bw = c.stringWidth(badge, FONT_B, 8.5) + 14
    bx = PAGE_W - MARGIN - bw
    c.setFillColor(colors.black)
    c.roundRect(bx, oy - 16, bw, 15, 3, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawCentredString(bx + bw / 2, oy - 12, badge)
    c.setFillColor(colors.black)
    return oy - 34


SINGLE_PAGE_FONT = 7.0  # the font size used to decide whether a puzzle fits
                          # on one combined page -- below this it's not worth
                          # the readability cost, so it gets the two-page
                          # spread instead


def _clue_geometry(puzzle, clue_top):
    """Shared geometry helper: returns (col1, col2, col_w, half)."""
    clues = puzzle["clues"]
    col_w = (PAGE_W - 2 * MARGIN - 0.25 * IN) / 2
    half = (len(clues) + 1) // 2
    return clues[:half], clues[half:], col_w, half


def _fits_combined_page(c, puzzle) -> bool:
    """Dry-run feasibility check: would this puzzle's clue list fit below
    its grid on one combined page, at a legible font, without crossing the
    bottom margin? Used to decide single-page vs two-page spread. Uses
    grid.compute_grid_geometry directly (not an approximation) so this can
    never drift out of sync with what draw_logic_grid actually renders."""
    from grid import compute_grid_geometry
    ox = MARGIN
    oy = PAGE_H - MARGIN
    intro_lines = _wrap(c, puzzle["intro"], FONT_I, 8.5, PAGE_W - 2 * MARGIN)
    intro_y = (oy - 34) - len(intro_lines) * 11
    grid_top = intro_y - 10

    geo = compute_grid_geometry(c, puzzle["categories"], trim="8.5x11")
    gh_bottom = grid_top - geo["total_h"]

    clue_top = gh_bottom - 14
    col1, col2, col_w, half = _clue_geometry(puzzle, clue_top)
    header_h = 13
    SAFETY_BUFFER = 8.0  # require this much slack beyond the true margin so
                          # borderline cases don't end up razor-thin in practice
    available_h = (clue_top - header_h) - MARGIN - SAFETY_BUFFER

    line_h = SINGLE_PAGE_FONT * 1.3
    gap = 2.0
    worst = 0
    for col_idx, col in enumerate((col1, col2)):
        h = 0
        for i, clue_text in enumerate(col):
            n_val = i + 1 if col_idx == 0 else half + i + 1
            lines = _wrap(c, f"{n_val}. {clue_text}", FONT, SINGLE_PAGE_FONT, col_w)
            h += len(lines) * line_h + gap
        worst = max(worst, h)
    return worst <= available_h


LAST_CLUE_BOTTOM = None


def draw_puzzle_page_combined(c: canvas.Canvas, puzzle: dict, puzzle_num_in_book: int):
    """Single-page layout: title, intro, grid, and clue list together.
    Only called for puzzles that pass _fits_combined_page."""
    global LAST_CLUE_BOTTOM
    LAST_CLUE_BOTTOM = None
    ox = MARGIN
    intro_y = _draw_header(c, puzzle, puzzle_num_in_book)
    c.setFont(FONT_I, 8.5)
    intro_lines = _wrap(c, puzzle["intro"], FONT_I, 8.5, PAGE_W - 2 * MARGIN)
    for line in intro_lines:
        c.drawString(ox, intro_y, line)
        intro_y -= 11

    grid_top = intro_y - 10
    gw, gh_bottom = draw_logic_grid(c, ox, grid_top, puzzle["categories"], trim="8.5x11")

    clue_top = gh_bottom - 14
    col1, col2, col_w, half = _clue_geometry(puzzle, clue_top)
    header_h = 13
    available_h = (clue_top - header_h) - MARGIN

    def total_height(font_size, line_h, gap):
        worst = 0
        for col_idx, col in enumerate((col1, col2)):
            h = 0
            for i, clue_text in enumerate(col):
                n_val = i + 1 if col_idx == 0 else half + i + 1
                lines = _wrap(c, f"{n_val}. {clue_text}", FONT, font_size, col_w)
                h += len(lines) * line_h + gap
            worst = max(worst, h)
        return worst

    font_size = SINGLE_PAGE_FONT
    line_h = font_size * 1.3
    gap = 2.0
    while font_size > 6.0 and total_height(font_size, line_h, gap) > available_h:
        font_size -= 0.25
        line_h = font_size * 1.3

    c.setFont(FONT_B, 9)
    c.drawString(ox, clue_top, "Clues")
    clue_top -= header_h

    for col_idx, col in enumerate((col1, col2)):
        cx = ox + col_idx * (col_w + 0.25 * IN)
        cy = clue_top
        for i, clue_text in enumerate(col):
            n = i + 1 if col_idx == 0 else half + i + 1
            lines = _wrap(c, f"{n}. {clue_text}", FONT, font_size, col_w)
            c.setFont(FONT, font_size)
            for line in lines:
                c.drawString(cx, cy, line)
                cy -= line_h
            cy -= gap
        LAST_CLUE_BOTTOM = cy if LAST_CLUE_BOTTOM is None else min(LAST_CLUE_BOTTOM, cy)


def draw_puzzle_grid_page(c: canvas.Canvas, puzzle: dict, puzzle_num_in_book: int):
    ox = MARGIN
    intro_y = _draw_header(c, puzzle, puzzle_num_in_book)

    c.setFont(FONT_I, 8.5)
    intro_lines = _wrap(c, puzzle["intro"], FONT_I, 8.5, PAGE_W - 2 * MARGIN)
    for line in intro_lines:
        c.drawString(ox, intro_y, line)
        intro_y -= 11

    grid_top = intro_y - 14
    draw_logic_grid(c, ox, grid_top, puzzle["categories"], trim="8.5x11")


def draw_puzzle_clues_page(c: canvas.Canvas, puzzle: dict, puzzle_num_in_book: int):
    global LAST_CLUE_BOTTOM
    LAST_CLUE_BOTTOM = None
    ox = MARGIN
    oy = _draw_header(c, puzzle, puzzle_num_in_book, suffix="\u2014 Clues")

    clues = puzzle["clues"]
    clue_top = oy - 20
    col_w = (PAGE_W - 2 * MARGIN - 0.25 * IN) / 2
    half = (len(clues) + 1) // 2
    col1, col2 = clues[:half], clues[half:]

    available_h = clue_top - MARGIN

    def total_height(font_size, line_h, gap):
        worst = 0
        for col_idx, col in enumerate((col1, col2)):
            h = 0
            for i, clue_text in enumerate(col):
                n_val = i + 1 if col_idx == 0 else half + i + 1
                lines = _wrap(c, f"{n_val}. {clue_text}", FONT, font_size, col_w)
                h += len(lines) * line_h + gap
            worst = max(worst, h)
        return worst

    font_size = CLUE_FONT_MAX
    line_h = font_size * 1.35
    gap = 6.0
    while font_size > CLUE_FONT_MIN and total_height(font_size, line_h, gap) > available_h:
        font_size -= 0.25
        line_h = font_size * 1.35

    for col_idx, col in enumerate((col1, col2)):
        cx = ox + col_idx * (col_w + 0.25 * IN)
        cy = clue_top
        for i, clue_text in enumerate(col):
            n = i + 1 if col_idx == 0 else half + i + 1
            lines = _wrap(c, f"{n}. {clue_text}", FONT, font_size, col_w)
            c.setFont(FONT, font_size)
            for line in lines:
                c.drawString(cx, cy, line)
                cy -= line_h
            cy -= gap
        LAST_CLUE_BOTTOM = cy if LAST_CLUE_BOTTOM is None else min(LAST_CLUE_BOTTOM, cy)


def draw_puzzle(c: canvas.Canvas, puzzle: dict, puzzle_num_in_book: int) -> int:
    """Always uses the two-page spread. Draws CLUES first, then GRID --
    this matters for book pagination: for the two pages to appear together
    on one open spread with the grid on the right (recto/odd), the clues
    page must land on the left (verso/even) immediately before it, not
    after. Drawing grid-then-clues put them on opposite sides of two
    DIFFERENT spreads instead (grid paired with the previous puzzle's
    trailing content, clues paired with the next puzzle's grid). Callers
    must ensure the page immediately before the first puzzle is called
    lands on an odd page count, so this first clues page opens on an even
    page (see ensure_recto_start() in make_volume.py / assemble_book.py).
    Handles its own showPage() calls. Returns the number of pages used."""
    draw_puzzle_clues_page(c, puzzle, puzzle_num_in_book)
    c.showPage()
    draw_puzzle_grid_page(c, puzzle, puzzle_num_in_book)
    c.showPage()
    return 2


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
