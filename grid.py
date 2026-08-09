"""
grid.py
─────────────────────────────────────────────────────────────────────────────
Triangular double-entry logic-grid renderer, styled to match the established
CJR Books / Julian Stone look (black kerned header bars, hairline gridlines,
boxed labels flush to the grid, no floating gaps) -- with DYNAMIC sizing on
top, so any (K categories x N items) shape sizes itself for 6x9 or 8.5x11
instead of needing new hand-tuned constants each time.

Font sizes are set to fixed READABLE targets (not derived from cell width --
that was the earlier bug: cell width barely constrains rotated-label font
size at all, so deriving font from cell produced needlessly tiny text).
row_label_w and col_label_h are instead measured from the actual longest
label string at the target font, so labels always fit without guessing.
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import fonts as _fonts

FONT   = _fonts.FONT_REGULAR
FONT_B = _fonts.FONT_BOLD

INK    = colors.Color(0.0, 0.0, 0.0)
HAIR   = colors.Color(0.55, 0.57, 0.60)   # thin gridline gray
HDR_BG = colors.black
HDR_FG = colors.white
SHADE  = colors.Color(0.955, 0.958, 0.965)  # boxed-label background

TRIMS = {
    "6x9":     (6 * IN, 9 * IN, 0.5 * IN, 0.5 * IN),
    "8.5x11":  (8.5 * IN, 11 * IN, 0.625 * IN, 0.625 * IN),
}

MIN_CELL = 0.20 * IN
MIN_CELL_LARGE_PRINT = 0.26 * IN

# Fixed readable font targets -- shrink only if the cell is genuinely too
# narrow to hold a character at that size (checked at render time).
ROW_FONT_TARGET = 8.5
COL_FONT_TARGET = 8.0
ROW_FONT_MIN = 6.5
COL_FONT_MIN = 6.5


def usable_width(trim: str) -> float:
    w, h, gutter, outer = TRIMS[trim]
    return w - gutter - outer


def _fit_font(c, font, target, min_size, max_char_h_budget):
    """Shrink font from target down to min_size only if a single character's
    height would exceed the available budget (cell width, for rotated text)."""
    size = target
    while size > min_size and size * 0.8 > max_char_h_budget:
        size -= 0.5
    return max(size, min_size)


def compute_cell_size(K: int, N: int, trim: str, large_print: bool = False,
                       usable_width_override: float = None) -> dict:
    """Rough cell pitch, used only as a sanity floor -- actual font sizes
    and label-area widths are resolved in draw_logic_grid with real text
    measurements. Pass usable_width_override to size a smaller illustrative
    grid (e.g. a worked example) instead of always filling the full page
    width regardless of how few columns exist."""
    usable = usable_width_override if usable_width_override is not None else usable_width(trim)
    cat_bar = 0.17 * IN
    approx_row_label_w = (1.05 + 0.05 * max(0, N - 5)) * IN
    ncols = (K - 1) * N
    avail = usable - cat_bar - approx_row_label_w
    cell = avail / ncols
    min_cell = MIN_CELL_LARGE_PRINT if large_print else MIN_CELL
    return {"cell": cell, "cat_bar": cat_bar, "fits": cell >= min_cell,
            "row_label_w": approx_row_label_w}


def fit_check(K: int, N: int, trim: str, large_print: bool = False,
              usable_width_override: float = None):
    spec = compute_cell_size(K, N, trim, large_print=large_print,
                              usable_width_override=usable_width_override)
    if not spec["fits"]:
        raise ValueError(
            f"{K} categories x {N} items does not fit legibly at {trim} "
            f"(cell would be {spec['cell']/IN:.3f}in). Use a larger trim or reduce N/K."
        )
    return spec


import re

def _display_label(s: str) -> str:
    """Clean a raw item string for grid display: drop a leading 'a/an/the'
    and title-case the rest, so 'a flower-draped stall' -> 'Flower-Draped
    Stall'. Clue text elsewhere is untouched -- this only affects what's
    printed inside the grid cells/labels."""
    s = re.sub(r"^(a|an|the)\s+", "", s.strip(), flags=re.IGNORECASE)
    # title-case each hyphenated part too ("flower-draped" -> "Flower-Draped")
    words = s.split(" ")
    out = []
    for w in words:
        parts = w.split("-")
        out.append("-".join(p[:1].upper() + p[1:] if p else p for p in parts))
    return " ".join(out)


def _draw_check(c, cx, cy, size):
    c.setStrokeColor(INK)
    c.setLineWidth(1.3)
    c.line(cx - size * 0.35, cy, cx - size * 0.08, cy - size * 0.32)
    c.line(cx - size * 0.08, cy - size * 0.32, cx + size * 0.4, cy + size * 0.35)


def _draw_x(c, cx, cy, size):
    c.setStrokeColor(HAIR)
    c.setLineWidth(1.1)
    c.line(cx - size * 0.3, cy - size * 0.3, cx + size * 0.3, cy + size * 0.3)
    c.line(cx - size * 0.3, cy + size * 0.3, cx + size * 0.3, cy - size * 0.3)


def _kerned_centered(c, cx, cy, text, font, size, tracking=0.6, color=HDR_FG):
    """Draw text with extra letter-spacing, centered at (cx, cy)."""
    widths = [c.stringWidth(ch, font, size) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    c.setFillColor(color)
    c.setFont(font, size)
    for ch, w in zip(text, widths):
        c.drawString(x, cy, ch)
        x += w + tracking


def compute_grid_geometry(c: canvas.Canvas, cats: dict, trim: str = "6x9",
                            large_print: bool = False, usable_width_override: float = None) -> dict:
    """Pure geometry calculation, no drawing -- the single source of truth
    for grid dimensions. draw_logic_grid uses this internally, and callers
    that need to know grid height in advance (e.g. deciding whether a
    puzzle's clue list will fit below it) should call this directly rather
    than re-approximating the math, which risks quietly drifting out of
    sync with what actually gets drawn."""
    names = list(cats.keys())
    K = len(names)
    N = len(next(iter(cats.values())))
    spec = fit_check(K, N, trim, large_print=large_print,
                      usable_width_override=usable_width_override)
    cell = spec["cell"]
    cat_bar = spec["cat_bar"]

    row_fsize = _fit_font(c, FONT, ROW_FONT_TARGET, ROW_FONT_MIN, cell * 0.9)
    col_fsize = _fit_font(c, FONT, COL_FONT_TARGET, COL_FONT_MIN, cell * 0.9)

    person_axis_labels = [_display_label(x) for x in cats[names[0]]]
    row_label_w = max(c.stringWidth(lbl, FONT, row_fsize) for lbl in person_axis_labels) + 10
    row_label_w = max(row_label_w, 0.55 * IN)

    col_items = [_display_label(it) for k in names[1:] for it in cats[k]]
    longest_col_label_w = max(c.stringWidth(lbl, FONT, col_fsize) for lbl in col_items)
    col_label_h = longest_col_label_w + 18

    n_blocks = K - 1
    total_h = cat_bar + col_label_h + n_blocks * N * cell
    total_w = (K - 1) * N * cell + cat_bar + row_label_w

    return {"cell": cell, "cat_bar": cat_bar, "row_fsize": row_fsize,
            "col_fsize": col_fsize, "row_label_w": row_label_w,
            "col_label_h": col_label_h, "n_blocks": n_blocks,
            "total_h": total_h, "total_w": total_w, "K": K, "N": N}


def draw_logic_grid(c: canvas.Canvas, ox: float, oy_top: float, cats: dict,
                     trim: str = "6x9", large_print: bool = False, marks: dict = None,
                     usable_width_override: float = None):
    """cats: ordered {category_name: [item labels]}. First category is the
    row/person axis. Returns (width, height) of the drawn grid.
    usable_width_override: constrain sizing to less than the full page width,
    e.g. for a small illustrative example grid that shouldn't stretch to
    fill the same width as a real, much-wider puzzle grid."""
    geo = compute_grid_geometry(c, cats, trim, large_print, usable_width_override)
    names = list(cats.keys())
    K, N = geo["K"], geo["N"]
    cell = geo["cell"]
    cat_bar = geo["cat_bar"]
    row_fsize = geo["row_fsize"]
    col_fsize = geo["col_fsize"]
    row_label_w = geo["row_label_w"]
    col_label_h = geo["col_label_h"]

    col_categories = names[1:]

    grid_x = ox + cat_bar + row_label_w
    catbar_y = oy_top
    collab_y = oy_top - cat_bar
    grid_top = collab_y - col_label_h

    # ---------- top category bars (black, kerned white text) ----------
    hdr_fsize = min(9.5, max(7, cell / IN * 26))
    for gi, cat_name in enumerate(col_categories):
        bx = grid_x + gi * N * cell
        block_w = N * cell
        c.setFillColor(HDR_BG)
        c.rect(bx, catbar_y - cat_bar, block_w, cat_bar, fill=1, stroke=0)
        if gi > 0:
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.2)
            c.line(bx, catbar_y - cat_bar, bx, catbar_y)
        _kerned_centered(c, bx + block_w / 2, catbar_y - cat_bar + cat_bar * 0.28,
                          cat_name.upper(), FONT_B, min(8.5, hdr_fsize), tracking=0.3)

    # ---------- rotated column item labels ----------
    c.setFillColor(INK)
    for gi, cat_name in enumerate(col_categories):
        for k, label in enumerate(cats[cat_name]):
            cxp = grid_x + (gi * N + k) * cell + cell / 2
            c.saveState()
            c.translate(cxp, grid_top - 0.03 * IN)
            c.rotate(90)
            c.setFont(FONT, col_fsize)
            c.drawString(6, -cell * 0.32, _display_label(label))
            c.restoreState()

    # ---------- staircase blocks: block i has rows = categories[i] ----------
    n_blocks = K - 1
    for block_idx in range(n_blocks):
        row_cat_name = names[block_idx]
        row_items = cats[row_cat_name]
        block_top = grid_top - block_idx * N * cell
        block_left = ox + cat_bar + row_label_w + block_idx * N * cell

        label_x = block_left - N * cell if block_idx > 0 else ox + cat_bar
        label_w = N * cell if block_idx > 0 else row_label_w

        # boxed, shaded row-label column, flush to the grid (no gap)
        c.setFillColor(SHADE)
        c.rect(label_x, block_top - N * cell, label_w, N * cell, fill=1, stroke=0)
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.5)
        for i in range(N + 1):
            yy = block_top - i * cell
            c.line(label_x, yy, label_x + label_w, yy)
        c.rect(label_x, block_top - N * cell, label_w, N * cell, fill=0, stroke=1)

        c.setFillColor(INK)
        c.setFont(FONT, row_fsize)
        for i, label in enumerate(row_items):
            yy = block_top - i * cell - cell / 2
            c.drawString(label_x + 4, yy - row_fsize * 0.35, _display_label(label))

        # the N x N cell blocks for this row category against remaining cols
        col_cats = names[block_idx + 1:]
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.5)
        for k, cat_name in enumerate(col_cats):
            gx0 = block_left + k * N * cell
            gy0 = block_top - N * cell
            for row in range(N + 1):
                yy = block_top - row * cell
                c.line(gx0, yy, gx0 + N * cell, yy)
            for col in range(N + 1):
                xx = gx0 + col * cell
                c.line(xx, gy0, xx, block_top)
            if marks:
                for row in range(N):
                    for col in range(N):
                        m = marks.get((row_cat_name, row, cat_name, col)) or \
                            marks.get((cat_name, col, row_cat_name, row))
                        if m:
                            ccx = gx0 + col * cell + cell / 2
                            ccy = block_top - row * cell - cell / 2
                            if m == "check":
                                _draw_check(c, ccx, ccy, cell * 0.7)
                            elif m == "x":
                                _draw_x(c, ccx, ccy, cell * 0.7)
            # heavier divider between this column-group and the next
            c.setStrokeColor(INK)
            c.setLineWidth(1.4)
            c.line(gx0 + N * cell, gy0, gx0 + N * cell, block_top)
            c.setStrokeColor(HAIR)
            c.setLineWidth(0.5)

        # heavier divider under this row-block, and around its label column
        c.setStrokeColor(INK)
        c.setLineWidth(1.4)
        c.line(block_left, block_top - N * cell, block_left + (len(col_cats)) * N * cell,
               block_top - N * cell)
        c.line(label_x, block_top - N * cell, label_x, block_top)
        c.line(label_x + label_w, block_top - N * cell, label_x + label_w, block_top)
        c.line(block_left, block_top, block_left + len(col_cats) * N * cell, block_top)

    grid_bottom = grid_top - n_blocks * N * cell

    # ---------- thin left accent bar (first block only) ----------
    c.setFillColor(HDR_BG)
    c.rect(ox, grid_top - N * cell, cat_bar, N * cell, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setStrokeColor(INK)
    total_w = (K - 1) * N * cell + cat_bar + row_label_w
    total_h = oy_top - grid_bottom
    return total_w, oy_top - total_h
