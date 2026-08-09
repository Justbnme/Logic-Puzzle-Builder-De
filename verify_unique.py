"""
verify_unique.py
─────────────────────────────────────────────────────────────────────────────
Independent uniqueness verifier. Deliberately does NOT import or reuse any
solving logic from puzzle_engine.py's _propagate() -- if that code has a
bug, checking uniqueness with the same code would just confirm its own
mistake. This is a from-scratch backtracking constraint solver that works
directly off the raw clue atoms, searches for solutions by brute-force
(with constraint-checking pruning, not the engine's arc-consistency), and
does NOT stop at the first solution found -- it keeps searching until
either a second distinct solution turns up (proof of non-uniqueness) or
the full search space is exhausted (proof of uniqueness).
"""

from typing import List, Tuple, Dict, Optional


def _parse_atoms(categories: List[str], N: int, atoms: List[Tuple]):
    """atoms as stored in Clue.atoms: (kind, catA, ia, catB, ib, offset)"""
    return atoms


def find_all_solutions(cat_names: List[str], N: int, anchor: str,
                        atoms: List[Tuple], max_solutions: int = 2) -> list:
    """Brute-force backtracking search, independent implementation.
    Returns up to max_solutions distinct complete assignments. Assignment
    is a dict {cat_name: [slot_for_item_0, slot_for_item_1, ...]}."""
    non_anchor = [c for c in cat_names if c != anchor]
    assignment: Dict[str, List[Optional[int]]] = {c: [None] * N for c in cat_names}
    assignment[anchor] = list(range(N))  # anchor fixed by construction

    # index atoms by which category-pairs they constrain, for quick lookup
    solutions = []

    def check_atom(kind, catA, ia, catB, ib, offset) -> Optional[bool]:
        """Returns True/False if determinable from current partial
        assignment, or None if not yet determinable (some slot unassigned)."""
        sa = assignment[catA][ia]
        sb = assignment[catB][ib]
        if sa is None or sb is None:
            return None
        if kind == "positive":
            return sa == sb
        if kind == "negative":
            return sa != sb
        if kind == "relative":
            return sa == sb + offset
        raise ValueError(kind)

    def consistent() -> bool:
        for (kind, catA, ia, catB, ib, offset) in atoms:
            r = check_atom(kind, catA, ia, catB, ib, offset)
            if r is False:
                return False
        return True

    def all_assigned(cat) -> bool:
        return all(s is not None for s in assignment[cat])

    def backtrack(cat_idx: int, item_idx: int) -> bool:
        """Returns True if search should stop (max_solutions reached)."""
        if cat_idx == len(non_anchor):
            # full assignment made -- record as a solution (verify total consistency)
            if consistent():
                solutions.append({c: list(assignment[c]) for c in cat_names})
            return len(solutions) >= max_solutions

        cat = non_anchor[cat_idx]
        if item_idx == N:
            return backtrack(cat_idx + 1, 0)

        used_slots = set(s for s in assignment[cat] if s is not None)
        for slot in range(N):
            if slot in used_slots:
                continue
            assignment[cat][item_idx] = slot
            if consistent():
                if backtrack(cat_idx, item_idx + 1):
                    assignment[cat][item_idx] = None
                    return True
            assignment[cat][item_idx] = None
        return False

    backtrack(0, 0)
    return solutions


def verify_puzzle_unique(cat_names: List[str], N: int, anchor: str,
                          clues) -> dict:
    """clues: list of Clue objects (from puzzle_engine). Returns a report dict."""
    atoms = [a for c in clues for a in c.atoms]
    solutions = find_all_solutions(cat_names, N, anchor, atoms, max_solutions=2)
    return {
        "n_solutions_found": len(solutions),
        "unique": len(solutions) == 1,
    }
