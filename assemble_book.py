import json
from reportlab.pdfgen import canvas
from render_page import draw_puzzle_page, PAGE_W, PAGE_H
from render_frontmatter import (draw_title_page, draw_copyright_page,
                                  draw_how_to_solve_page, draw_worked_example_page,
                                  draw_worked_example_grid_page)
from render_backmatter import draw_solutions_pages

with open("master_logic_vol1.json") as f:
    puzzles = json.load(f)

c = canvas.Canvas("master_logic_vol1_FULL.pdf", pagesize=(PAGE_W, PAGE_H))

draw_title_page(c); c.showPage()
draw_copyright_page(c); c.showPage()
draw_how_to_solve_page(c); c.showPage()
draw_worked_example_page(c); c.showPage()
draw_worked_example_grid_page(c); c.showPage()

for p in puzzles:
    draw_puzzle_page(c, p, p["puzzle_index"])
    c.showPage()

draw_solutions_pages(c, puzzles)
c.showPage()

c.save()
print(f"Assembled full book: 5 front matter + {len(puzzles)} puzzles + solutions")
