"""
grid.py
─────────────────────────────────────────────────────────────────────────────
Triangular double-entry logic-grid renderer with DYNAMIC sizing.

The old grid.py (Logic Plain & Simple) had fixed cell/font sizes tuned by
hand per category count at one trim size (6x9). This version computes cell
size, font size, and label-box dimensions from the actual (K categories x N
items) shape and the page's usable width, for any trim size -- so a 7-item
category at 8.5x11 sizes itself correctly instead of needing new constants
hand-tuned each time.

Usage:
    from grid import draw_logic_grid, fit_check
    fit_check(K, N, trim="8.5x11")   # raises if it won't fit legibly
    w, h = draw_logic_grid(c, ox, oy_top, cats)  # cats: {name: [items]}
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white, HexColor

TRIMS = {
    "6x9":     (6 * IN, 9 * IN, 0.5 * IN, 0.5 * IN),   # w, h, gutter, outer margin
    "8.5x11":  (8.5 * IN, 11 * IN, 0.625 * IN, 0.625 * IN),
}

MIN_CELL = 0.20 * IN          # below this, checkmarks/x's stop being legible
MIN_CELL_LARGE_PRINT = 0.26 * IN

CREAM = HexColor("#FBF7EF")
SLATE = HexColor("#3C4A5C")


def usable_width(trim: str) -> float:
    w, h, gutter, outer = TRIMS[trim]
    return w - gutter - outer


def compute_cell_size(K: int, N: int, trim: str, row_label_w: float = None,
                       large_print: bool = False) -> dict:
    """Given K categories and N items/category, compute a cell size that
    fits the page. The grid has (K-1) blocks across, each N columns wide,
    plus one row-label column and one thin category-bar column."""
    usable = usable_width(trim)
    cat_bar = 0.20 * IN
    if row_label_w is None:
        # heuristic: longer item labels need more room; scale gently with N
        row_label_w = (1.0 + 0.03 * max(0, N - 5)) * IN
    ncols = (K - 1) * N
    avail = usable - cat_bar - row_label_w
    cell = avail / ncols
    min_cell = MIN_CELL_LARGE_PRINT if large_print else MIN_CELL
    fits = cell >= min_cell
    # font scales with cell, capped
    font_size = max(6, min(11, cell / IN * 26))
    return {
        "cell": max(cell, min_cell * 0.6),  # never render literally unreadable
        "row_label_w": row_label_w,
        "cat_bar": cat_bar,
        "font_size": font_size,
        "fits": fits,
        "ncols": ncols,
    }


def fit_check(K: int, N: int, trim: str, large_print: bool = False):
    spec = compute_cell_size(K, N, trim, large_print=large_print)
    if not spec["fits"]:
        raise ValueError(
            f"{K} categories x {N} items does not fit legibly at {trim} "
            f"(cell would be {spec['cell']/IN:.3f}in, need >= "
            f"{(MIN_CELL_LARGE_PRINT if large_print else MIN_CELL)/IN:.3f}in). "
            f"Use a larger trim size or reduce N/K."
        )
    return spec


def draw_logic_grid(c: canvas.Canvas, ox: float, oy_top: float, cats: dict,
                     trim: str = "6x9", large_print: bool = False):
    """cats: ordered dict {category_name: [item labels]}. First category is
    the row axis (people); remaining categories form the staircase blocks."""
    names = list(cats.keys())
    K = len(names)
    N = len(next(iter(cats.values())))
    spec = fit_check(K, N, trim, large_print=large_print)
    cell = spec["cell"]
    row_label_w = spec["row_label_w"]
    cat_bar = spec["cat_bar"]
    fsize = spec["font_size"]

    row_names = cats[names[0]]
    col_categories = names[1:]  # each becomes one staircase block, N cols wide

    # column label height (rotated text) -- scale with longest label roughly
    col_label_h = (0.85 + 0.05 * max(0, N - 5)) * IN

    x0 = ox
    y0 = oy_top - col_label_h

    # -- column headers (rotated), grouped per category with a black kerned bar --
    c.setFont("Helvetica-Bold", fsize)
    bx = x0 + cat_bar + row_label_w
    for cat_name in col_categories:
        block_w = N * cell
        c.setFillColor(SLATE)
        c.rect(bx, y0, block_w, 0.16 * IN, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", fsize - 1)
        c.drawCentredString(bx + block_w / 2, y0 + 0.04 * IN, cat_name.upper())
        c.setFillColor(black)
        for i, label in enumerate(cats[cat_name]):
            cx = bx + i * cell + cell / 2
            c.saveState()
            c.translate(cx, y0 - 0.02 * IN)
            c.rotate(90)
            c.setFont("Helvetica", fsize - 1)
            c.drawString(2, -cell * 0.3, label)
            c.restoreState()
        bx += block_w

    # -- staircase blocks: block i has rows = categories[i], columns = categories[i+1:] --
    n_blocks = len(names) - 1  # e.g. K=4 categories -> 3 blocks
    grid_top = y0
    c.setFont("Helvetica", fsize)
    for block_idx in range(n_blocks):
        row_cat_name = names[block_idx]
        row_items = cats[row_cat_name]
        block_top = grid_top - block_idx * N * cell
        block_left = x0 + cat_bar + row_label_w + block_idx * N * cell

        # row labels for this block, reusing the strip its own category
        # occupied as a column header one step up (the classic staircase look)
        label_x = block_left - N * cell if block_idx > 0 else x0 + cat_bar
        label_w = N * cell if block_idx > 0 else row_label_w
        c.setFillColor(SLATE)
        c.rect(label_x, block_top - N * cell, label_w, N * cell, fill=1, stroke=0)
        c.setFillColor(white)
        for i, label in enumerate(row_items):
            yy = block_top - i * cell - cell / 2
            c.drawString(label_x + 3, yy - fsize * 0.35, label[:24])
        c.setFillColor(black)

        # the actual N x N cell blocks for this row category against every
        # remaining column category
        col_cats = names[block_idx + 1:]
        for k, cat_name in enumerate(col_cats):
            for row in range(N):
                for col in range(N):
                    cxL = block_left + k * N * cell + col * cell
                    cyB = block_top - (row + 1) * cell
                    c.rect(cxL, cyB, cell, cell, stroke=1, fill=0)

    grid_bottom = grid_top - n_blocks * N * cell

    c.setFillColor(SLATE)
    c.rect(x0, grid_top - N * cell, cat_bar, N * cell, fill=1, stroke=0)
    c.setFillColor(black)

    c.setStrokeColor(black)
    total_w = (K - 1) * N * cell + cat_bar + row_label_w
    total_h = (oy_top - grid_bottom)
    return total_w, oy_top - total_h
