# logic-puzzle-engine

Flexible logic-grid puzzle engine for CJR Books / Deduction House.

Replaces the old N=5-hardwired engine. Supports:
- Any item count per category (N) -- tested 5, 6, 7
- Any category count (K >= 3)
- Clue types: direct positive/negative, either/or, relative-order
  (ordinal axis, e.g. "exactly 1 floor above"), compound (bundled clues)
- Pure-deduction solver: puzzles are only accepted if arc-consistency
  propagation alone solves them -- no guessing/branching required, matching
  the "no guessing ever required" standard these books are sold on
- Dynamic cell/font sizing (grid.py) for any trim size, not hand-tuned
  constants per category count

## Status (as of this build)
- puzzle_engine.py: built and tested across N=5/6/7, K=3/4, all four
  difficulty profiles (easy/medium/hard/expert) -- all combinations solve
  via pure deduction.
- grid.py: dynamic sizing works, renders without errors. Visual styling
  (kerned header bars, boxed labels flush to grid) is a functional first
  pass, NOT yet matched to the established Pure Logic / Logic Plain &
  Simple look -- needs a styling pass same as before.
- Clue text templates are functional but need a language/grammar polish
  pass before anything goes to print.

## Files
- puzzle_engine.py -- Category/PuzzleEngine classes, clue generation, solver
- grid.py -- renderer, dynamic cell/font sizing per trim size
- requirements.txt

## Next steps
1. Polish clue phrasing templates (grammar, natural language per clue type)
2. Style pass on grid.py to match established Pure Logic visual identity
3. Build a themed word-list/scenario module (like themes_mystery.py) for
   whichever line this feeds -- e.g. a Hard & Expert spinoff at 8.5x11
