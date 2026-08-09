"""
render_frontmatter.py
─────────────────────────────────────────────────────────────────────────────
Title page, copyright page, How to Solve guide, and a worked example --
all original content/wording (not derived from any competitor text).
"""

from reportlab.lib.units import inch as IN
from reportlab.pdfgen import canvas
from reportlab.lib import colors

PAGE_W, PAGE_H = 8.5 * IN, 11 * IN
MARGIN = 0.75 * IN


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


def _draw_wrapped(c, text, x, y, font, size, max_width, leading):
    lines = _wrap(c, text, font, size, max_width)
    for line in lines:
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_title_page(c, title="MASTER LOGIC", subtitle="Volume 1",
                     tagline="50 Hard + 50 Expert Logic Grid Puzzles for Adults",
                     byline="Julian Stone", imprint="Deduction House"):
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 3.2 * IN, title)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 3.75 * IN, subtitle.upper())

    c.setLineWidth(1)
    c.line(PAGE_W / 2 - 1.4 * IN, PAGE_H - 4.05 * IN, PAGE_W / 2 + 1.4 * IN, PAGE_H - 4.05 * IN)

    c.setFont("Helvetica", 13)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 4.5 * IN, tagline)

    c.setFont("Helvetica", 15)
    c.drawCentredString(PAGE_W / 2, MARGIN + 1.0 * IN, byline)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(PAGE_W / 2, MARGIN + 0.75 * IN, imprint)


def draw_copyright_page(c, byline="Julian Stone", imprint="Deduction House",
                         year="2026"):
    c.setFont("Helvetica", 9)
    y = PAGE_H - 5.2 * IN
    x = MARGIN
    w = PAGE_W - 2 * MARGIN
    lines = [
        f"Master Logic, Volume 1",
        f"Copyright \u00A9 {year} {byline} / {imprint}",
        "",
        "All rights reserved. No part of this publication may be reproduced, "
        "distributed, or transmitted in any form or by any means, including "
        "photocopying, recording, or other electronic or mechanical methods, "
        "without prior written permission of the publisher, except in the case "
        "of brief quotations embodied in critical reviews and certain other "
        "noncommercial uses permitted by copyright law.",
        "",
        "This is a work of original puzzle content. Names and scenarios used "
        "throughout are fictional; any resemblance to actual persons, living "
        "or dead, is purely coincidental.",
        "",
        "First Edition",
    ]
    for para in lines:
        if para == "":
            y -= 10
            continue
        y = _draw_wrapped(c, para, x, y, "Helvetica", 9, w, 12.5)
        y -= 4


def draw_how_to_solve_page(c):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, PAGE_H - MARGIN - 10, "How to Solve These Puzzles")
    y = PAGE_H - MARGIN - 45
    w = PAGE_W - 2 * MARGIN

    sections = [
        (None, "Every puzzle in this book is a logic grid puzzle. A short setup "
                "tells you which categories are involved, and your job is to work "
                "out the one and only arrangement that fits every clue. No "
                "guessing is ever needed: each puzzle has a single solution "
                "reachable through pure deduction."),
        ("Reading the grid",
         "The grid pairs every item in one category against every item in "
         "another. Each small square asks a single yes-or-no question: does "
         "this pairing hold? Mark an X when a clue rules a pairing out, and a "
         "checkmark once you've confirmed one. The moment a pairing is "
         "confirmed, X out the rest of that row and column within the same "
         "block, since an item can only match one item in each other category."),
        ("A simple method",
         "Start with the most concrete clues, meaning direct statements that "
         "hand you a pairing outright. Then work the relational clues: "
         "either/or statements, comparisons, and exact-position relationships. "
         "Each mark you make narrows the others. Keep cross-referencing "
         "between blocks, since a deduction in one pair of categories will "
         "often unlock another."),
        ("Difficulty",
         "This volume is Hard and Expert throughout: puzzles 1 to 50 are "
         "Hard, and 51 to 100 are Expert. Expert puzzles lean more heavily on "
         "either/or reasoning, exact-position clues, and clues that bundle "
         "several facts together, with fewer clues handed to you outright."),
        (None, "Full solutions for every puzzle are at the back of the book."),
    ]
    for heading, body in sections:
        if heading:
            c.setFont("Helvetica-Bold", 11.5)
            c.drawString(MARGIN, y, heading)
            y -= 16
        y = _draw_wrapped(c, body, MARGIN, y, "Helvetica", 10, w, 14)
        y -= 14


def draw_worked_example_page(c):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, PAGE_H - MARGIN - 10, "A Worked Example")
    y = PAGE_H - MARGIN - 40
    w = PAGE_W - 2 * MARGIN

    intro = ("Here's a small puzzle solved one step at a time. Three friends, "
             "Priya, Owen, and Talia, each chose a different pastry and a "
             "different drink.")
    y = _draw_wrapped(c, intro, MARGIN, y, "Helvetica", 10, w, 14)
    y -= 10

    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(MARGIN, y, "Clues")
    y -= 14
    clues = [
        "1. Priya chose the muffin.",
        "2. The croissant was paired with tea.",
        "3. Owen did not drink coffee.",
        "4. Talia drank cocoa.",
    ]
    for cl in clues:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, cl)
        y -= 13.5
    y -= 12

    steps = [
        ("Step 1: Place the given.",
         "Clue 1 hands us a direct pairing: Priya chose the muffin. Mark it, "
         "and X out the rest of Priya's row and the muffin's column."),
        ("Step 2: Another direct pairing.",
         "Clue 2 pairs the croissant with tea. Mark it, and X out the rest of "
         "that row and column."),
        ("Step 3: Cross-reference.",
         "Clue 4 says Talia drank cocoa, not tea. Since the croissant is "
         "already paired with tea, Talia can't be the croissant person, so "
         "Talia must have the scone. That leaves the croissant for Owen."),
        ("Step 4: Finish by elimination.",
         "Owen now has the croissant and, from Step 2, tea, which also "
         "satisfies Clue 3 (Owen didn't drink coffee). The only drink left "
         "for Priya is coffee."),
    ]
    for heading, body in steps:
        c.setFont("Helvetica-Bold", 10.5)
        y = _draw_wrapped(c, heading, MARGIN, y, "Helvetica-Bold", 10.5, w, 14)
        y = _draw_wrapped(c, body, MARGIN, y, "Helvetica", 10, w, 14)
        y -= 10

    y -= 6
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(MARGIN, y, "Solved:")
    y -= 15
    c.setFont("Helvetica", 10)
    solved = [
        "Priya - muffin - coffee",
        "Owen - croissant - tea",
        "Talia - scone - cocoa",
    ]
    for line in solved:
        c.drawString(MARGIN + 10, y, line)
        y -= 14

    y -= 10
    closing = ("That's the whole method: place what you're given directly, then "
               "let each new fact narrow the rest, until every square is "
               "decided. New to logic grids? Give Puzzle 1 a try next.")
    _draw_wrapped(c, closing, MARGIN, y, "Helvetica-Oblique", 9.5, w, 13)
