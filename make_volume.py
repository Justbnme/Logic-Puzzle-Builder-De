import sys
import json
from reportlab.pdfgen import canvas
import build_volume
from verify_unique import verify_puzzle_unique
from render_page import draw_puzzle_page, PAGE_W, PAGE_H
from render_frontmatter import (draw_title_page, draw_copyright_page,
                                  draw_how_to_solve_page, draw_worked_example_page)
from render_backmatter import draw_solutions_pages


def make_volume(volume_number: int):
    subtitle = f"Volume {volume_number}"
    print(f"=== Building Master Logic, {subtitle} ===")

    puzzles = build_volume.build_volume(volume_number=volume_number, verify=True)
    build_volume.report(puzzles)

    # extra audits, same checks used for Volume 1
    dupe_text = [p["puzzle_index"] for p in puzzles if len(set(p["clues"])) != len(p["clues"])]
    hard_over = [p["puzzle_index"] for p in puzzles
                 if p["difficulty"] == "hard" and p["direct_fraction"] > 0.45]
    expert_over = [p["puzzle_index"] for p in puzzles
                   if p["difficulty"] == "expert" and p["direct_fraction"] > 0.20]
    non_unique = [p["puzzle_index"] for p in puzzles if not p["unique_solution"]]
    print(f"Duplicate clue text: {len(dupe_text)} {dupe_text if dupe_text else ''}")
    print(f"Hard puzzles over direct-fraction cap: {len(hard_over)} {hard_over if hard_over else ''}")
    print(f"Expert puzzles over direct-fraction cap: {len(expert_over)} {expert_over if expert_over else ''}")
    print(f"Non-unique solutions: {len(non_unique)} {non_unique if non_unique else ''}")

    json_path = f"master_logic_vol{volume_number}.json"
    with open(json_path, "w") as f:
        json.dump(puzzles, f, indent=1)

    pdf_path = f"master_logic_vol{volume_number}_FULL.pdf"
    c = canvas.Canvas(pdf_path, pagesize=(PAGE_W, PAGE_H))
    draw_title_page(c, subtitle=subtitle); c.showPage()
    draw_copyright_page(c, subtitle=subtitle); c.showPage()
    draw_how_to_solve_page(c); c.showPage()
    draw_worked_example_page(c); c.showPage()
    for p in puzzles:
        draw_puzzle_page(c, p, p["puzzle_index"])
        c.showPage()
    draw_solutions_pages(c, puzzles)
    c.showPage()
    c.save()

    from pypdf import PdfReader
    n_pages = len(PdfReader(pdf_path).pages)
    print(f"Saved {pdf_path} ({n_pages} pages) and {json_path}")
    return {"ok": not (dupe_text or hard_over or expert_over or non_unique), "pages": n_pages}


if __name__ == "__main__":
    vol = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    make_volume(vol)
