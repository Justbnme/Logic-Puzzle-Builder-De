"""
grid.py
─────────────────────────────────────────────────────────────────────────────
Triangular double-entry logic-grid renderer, styled to match the established
CJR Books / Julian Stone look (black kerned header bars, hairline gridlines,
boxed labels flush to the grid, no floating gaps) -- with DYNAMIC sizing on
top, so any (K categories x N items) shape sizes itself for 6x9 or 8.5x11
instead of needing new hand-tuned constants each time.
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors

INK    = colors.Color(0.0, 0.0, 0.0)
HAIR   = colors.Color(0.55, 0.57, 0.60)   # thin gridline gray
HDR_BG = colors.black
HDR_FG = colors.white
SHADE  = colors.Color(0.955, 0.958, 0.965)  # boxed-label background

FONT   = "Helvetica"
FONT_B = "Helvetica-Bold"

TRIMS = {
    "6x9":     (6 * IN, 9 * IN, 0.5 * IN, 0.5 * IN),
    "8.5x11":  (8.5 * IN, 11 * IN, 0.625 * IN, 0.625 * IN),
}

MIN_CELL = 0.20 * IN
MIN_CELL_LARGE_PRINT = 0.26 * IN


def usable_width(trim: str) -> float:
    w, h, gutter, outer = TRIMS[trim]
    return w - gutter - outer


def compute_cell_size(K: int, N: int, trim: str, row_label_w: float = None,
                       large_print: bool = False) -> dict:
    usable = usable_width(trim)
    cat_bar = 0.17 * IN
    if row_label_w is None:
        row_label_w = (0.95 + 0.045 * max(0, N - 5)) * IN
    ncols = (K - 1) * N
    avail = usable - cat_bar - row_label_w
    cell = avail / ncols
    min_cell = MIN_CELL_LARGE_PRINT if large_print else MIN_CELL
    fits = cell >= min_cell
    font_size = max(6, min(9.5, cell / IN * 24))
    return {
        "cell": max(cell, min_cell * 0.6),
        "row_label_w": row_label_w,
        "cat_bar": cat_bar,
        "font_size": font_size,
        "fits": fits,
    }


def fit_check(K: int, N: int, trim: str, large_print: bool = False):
    spec = compute_cell_size(K, N, trim, large_print=large_print)
    if not spec["fits"]:
        raise ValueError(
            f"{K} categories x {N} items does not fit legibly at {trim} "
            f"(cell would be {spec['cell']/IN:.3f}in, need >= "
            f"{(MIN_CELL_LARGE_PRINT if large_print else MIN_CELL)/IN:.3f}in)."
        )
    return spec


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


def draw_logic_grid(c: canvas.Canvas, ox: float, oy_top: float, cats: dict,
                     trim: str = "6x9", large_print: bool = False):
    """cats: ordered {category_name: [item labels]}. First category is the
    row/person axis. Returns (width, height) of the drawn grid."""
    names = list(cats.keys())
    K = len(names)
    N = len(next(iter(cats.values())))
    spec = fit_check(K, N, trim, large_print=large_print)
    cell = spec["cell"]
    row_label_w = spec["row_label_w"]
    cat_bar = spec["cat_bar"]
    fsize = spec["font_size"]
    small_fsize = max(5.5, fsize - 1.3)

    col_categories = names[1:]
    col_label_h = (0.80 + 0.045 * max(0, N - 5)) * IN

    grid_x = ox + cat_bar + row_label_w
    catbar_y = oy_top
    collab_y = oy_top - cat_bar
    grid_top = collab_y - col_label_h

    # ---------- top category bars (black, kerned white text) ----------
    for gi, cat_name in enumerate(col_categories):
        bx = grid_x + gi * N * cell
        block_w = N * cell
        c.setFillColor(HDR_BG)
        c.rect(bx, catbar_y - cat_bar, block_w, cat_bar, fill=1, stroke=0)
        _kerned_centered(c, bx + block_w / 2, catbar_y - cat_bar + cat_bar * 0.28,
                          cat_name.upper(), FONT_B, min(8.5, fsize), tracking=0.7)

    # ---------- rotated column item labels ----------
    c.setFillColor(INK)
    for gi, cat_name in enumerate(col_categories):
        for k, label in enumerate(cats[cat_name]):
            cxp = grid_x + (gi * N + k) * cell + cell / 2
            c.saveState()
            c.translate(cxp, grid_top - 0.03 * IN)
            c.rotate(90)
            c.setFont(FONT, small_fsize)
            c.drawString(2, -cell * 0.28, label[:24])
            c.restoreState()

    # ---------- staircase blocks: block i has rows = categories[i] ----------
    n_blocks = K - 1
    c.setFont(FONT, fsize)
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
        c.setFont(FONT, fsize)
        for i, label in enumerate(row_items):
            yy = block_top - i * cell - cell / 2
            c.drawString(label_x + 4, yy - fsize * 0.35, label[:26])

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

    grid_bottom = grid_top - n_blocks * N * cell

    # ---------- thin left accent bar (first block only) ----------
    c.setFillColor(HDR_BG)
    c.rect(ox, grid_top - N * cell, cat_bar, N * cell, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setStrokeColor(INK)
    total_w = (K - 1) * N * cell + cat_bar + row_label_w
    total_h = oy_top - grid_bottom
    return total_w, oy_top - total_h
