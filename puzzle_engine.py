"""
puzzle_engine.py
─────────────────────────────────────────────────────────────────────────────
Flexible logic-grid puzzle engine.

Replaces the old N=5-hardwired engine. Categories can have ANY item count
(N), and there can be any number of categories (K >= 3). Difficulty is
still controlled by clue *profile* (which clue types + how sparse), matching
the philosophy already validated in Logic Plain & Simple and Mystery Case
Files -- this version just removes the N=5 ceiling and adds two new clue
types: relative-order (ordinal axis) and compound (bundled clues).

Core model
──────────
There are N hidden "entities" (slots 0..N-1). Every category is a bijection
between its items and these slots. One category may be marked `ordinal=True`
(e.g. Floor, Place, Rank) -- its items are, by construction, assigned to
slots in index order (item i -> slot i). This is what makes relative-order
clues ("exactly 1 floor above") solvable by simple constraint propagation
instead of search: the ordinal category IS the slot axis.

Clue types
──────────
  direct_positive   itemA (catA) is itemB (catB)
  direct_negative    itemA (catA) is NOT itemB (catB)
  either_or          itemA (catA) is either itemB1 or itemB2 (catB)
  relative_order      itemA is exactly `offset` positions above/below itemB
                      on the ordinal axis (requires a category marked ordinal)
  compound            2-3 atomic clues bundled into one printed clue
                      ("All of these are true: ...")

Solver
──────
Pure arc-consistency propagation (no branching/guessing) over per-item
possible-slot sets, plus a brute-force uniqueness check used only to CONFIRM
a puzzle has one solution before we start adding clues -- never to solve it
for the reader. A puzzle is only accepted if propagation alone (no search)
narrows every item to a single slot. That mirrors the "no guessing ever
required" claim these books make.
"""

from __future__ import annotations
import random
import itertools
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class Category:
    name: str                 # e.g. "Guest", "Floor"
    items: List[str]          # display labels, e.g. ["the Envoy", "the Curator", ...]
    ordinal: bool = False      # True for the fixed slot-order axis (Floor, Place, Rank)
    kind: str = "attribute"    # "person" | "ordinal" | "attribute" -- drives clue grammar
    verb: str = "had"          # used for attribute categories, e.g. "wore", "was holding"
    unit: str = None           # used for ordinal categories, e.g. "floor", "place"
    possessive: str = ""       # optional possessive determiner baked into the verb phrase,
                                # e.g. verb="lost", possessive="their" -> "lost their {item}".
                                # Kept separate from verb so either/or clues can repeat the
                                # possessive per alternative instead of stranding it before
                                # "either" (e.g. "lost either their X or their Y", not
                                # "lost their either X or Y").

    def __post_init__(self):
        if self.ordinal and self.kind == "attribute":
            self.kind = "ordinal"
        if self.kind == "ordinal" and self.unit is None:
            self.unit = self.name.rstrip("s").lower()

    @property
    def n(self) -> int:
        return len(self.items)

    def _verb_phrase(self) -> str:
        """Full verb phrase including any possessive, e.g. 'lost their'."""
        if self.possessive:
            return f"{self.verb} {self.possessive}"
        return self.verb

    def as_subject(self, item_idx: int) -> str:
        it = self.items[item_idx]
        if self.kind == "person":
            return it[0].upper() + it[1:] if it and it[0].islower() else it
        if self.kind == "ordinal":
            return f"Whoever was on {self.unit} {it}"
        return f"Whoever {self._verb_phrase()} {it}"

    def as_predicate(self, item_idx: int) -> str:
        it = self.items[item_idx]
        if self.kind == "person":
            return f"is {it}"
        if self.kind == "ordinal":
            return f"is on {self.unit} {it}"
        return f"{self._verb_phrase()} {it}"

    def as_bare_object(self, item_idx: int) -> str:
        """Plain object form, used only when a single neutral copula ('is
        either...or') already governs the sentence (person/ordinal). Not
        safe for attribute categories -- see as_object_clause."""
        it = self.items[item_idx]
        if self.kind == "ordinal":
            return f"on {self.unit} {it}"
        return it

    def as_object_clause(self, item_idx: int) -> str:
        """Object-position form for negative direct clues ('X is not ___'),
        safe for any kind -- attribute categories get a full relative-clause
        object ('the one who lost their X') instead of a bare noun, so the
        verb is never silently dropped."""
        it = self.items[item_idx]
        if self.kind == "person":
            return it
        if self.kind == "ordinal":
            return f"on {self.unit} {it}"
        return f"the one who {self._verb_phrase()} {it}"

    def either_or_phrase(self, i1: int, i2: int) -> str:
        """Full '<verb> either A or B' clause for either/or clues, safe for
        any kind -- attribute categories with a possessive repeat it per
        alternative instead of stranding it before 'either'."""
        if self.kind == "attribute":
            poss = f"{self.possessive} " if self.possessive else ""
            it1, it2 = self.items[i1], self.items[i2]
            return f"{self.verb} either {poss}{it1} or {poss}{it2}"
        obj1, obj2 = self.as_bare_object(i1), self.as_bare_object(i2)
        return f"{self.stem()} either {obj1} or {obj2}"

    def stem(self) -> str:
        """The bare copula/verb used before a plain object list, e.g. in
        'X wore either A or B' / 'X is either C or D'."""
        if self.kind == "attribute":
            return self.verb
        return "is"


@dataclass
class Clue:
    kind: str                 # "positive" | "negative" | "either_or" | "relative" | "compound"
    text: str
    # atomic constraints this clue applies to the solver, as a list of
    # ("positive"|"negative"|"relative", cat_a, item_a, cat_b, item_b, offset_or_None)
    atoms: List[Tuple] = field(default_factory=list)


class PuzzleEngine:
    def __init__(self, categories: List[Category], seed: Optional[int] = None):
        ns = {c.n for c in categories}
        if len(ns) != 1:
            raise ValueError(f"All categories must have the same item count (got {ns})")
        self.N = ns.pop()
        if self.N < 3:
            raise ValueError("Need at least 3 items per category")
        if len(categories) < 3:
            raise ValueError("Need at least 3 categories")
        self.categories = categories
        self.cat_by_name = {c.name: c for c in categories}
        self.ordinal_cat = next((c for c in categories if c.ordinal), None)
        # Every puzzle needs one internal anchor category (item i -> slot i,
        # fixed) so relational clues have a reference to converge against.
        # Prefer the ordinal category (Floor/Place) since that also gives
        # relative-order clues real meaning; otherwise just use the first
        # category as an arbitrary internal bookkeeping anchor -- this is
        # never exposed to the reader, only item-to-item clues are printed.
        self.anchor_cat = self.ordinal_cat or self.categories[0]
        self.rng = random.Random(seed)
        self.solution: Dict[str, List[int]] = {}   # cat.name -> [slot for item i]
        self._generate_solution()

    # -- solution -----------------------------------------------------------
    def _generate_solution(self):
        for c in self.categories:
            if c.ordinal:
                self.solution[c.name] = list(range(self.N))
            else:
                perm = list(range(self.N))
                self.rng.shuffle(perm)
                self.solution[c.name] = perm

    def slot_of(self, cat: str, item_idx: int) -> int:
        return self.solution[cat][item_idx]

    def item_at_slot(self, cat: str, slot: int) -> int:
        return self.solution[cat].index(slot)

    # -- clue generation ------------------------------------------------------
    def _other_cat(self, exclude: List[str]) -> Category:
        pool = [c for c in self.categories if c.name not in exclude]
        return self.rng.choice(pool)

    def gen_direct(self, positive: bool) -> Clue:
        catA, catB = self.rng.sample(self.categories, 2)
        ia = self.rng.randrange(self.N)
        sa = self.slot_of(catA.name, ia)
        if positive:
            ib = self.item_at_slot(catB.name, sa)
            text = f"{catA.as_subject(ia)} {catB.as_predicate(ib)}."
            atoms = [("positive", catA.name, ia, catB.name, ib, None)]
        else:
            correct_ib = self.item_at_slot(catB.name, sa)
            wrong_choices = [j for j in range(self.N) if j != correct_ib]
            ib = self.rng.choice(wrong_choices)
            text = f"{catA.as_subject(ia)} is not {catB.as_object_clause(ib)}."
            atoms = [("negative", catA.name, ia, catB.name, ib, None)]
        return Clue("positive" if positive else "negative", text, atoms)

    def gen_either_or(self) -> Clue:
        catA, catB = self.rng.sample(self.categories, 2)
        ia = self.rng.randrange(self.N)
        sa = self.slot_of(catA.name, ia)
        correct_ib = self.item_at_slot(catB.name, sa)
        others = [j for j in range(self.N) if j != correct_ib]
        wrong_ib = self.rng.choice(others)
        pair = [correct_ib, wrong_ib]
        self.rng.shuffle(pair)
        text = f"{catA.as_subject(ia)} {catB.either_or_phrase(pair[0], pair[1])}."
        atoms = [("negative", catA.name, ia, catB.name, j, None)
                 for j in range(self.N) if j not in pair]
        return Clue("either_or", text, atoms)

    def gen_relative(self, max_offset: int = None) -> Optional[Clue]:
        if max_offset is None:
            max_offset = self.N - 1
        if self.ordinal_cat is None:
            return None
        non_ord = [c for c in self.categories if not c.ordinal]
        catA = self.rng.choice(non_ord)
        ia = self.rng.randrange(self.N)
        sa = self.slot_of(catA.name, ia)
        candidates = []
        for offset in range(1, max_offset + 1):
            sb = sa - offset
            if 0 <= sb < self.N:
                ib = self.item_at_slot(catA.name, sb)
                candidates.append((offset, ib))
        if not candidates:
            return None
        offset, ib = self.rng.choice(candidates)
        unit = self.ordinal_cat.unit
        plural = "s" if offset != 1 else ""
        # Build a clean comparison sentence: "<A> was exactly N <unit>s above <B>."
        subj_text = catA.items[ia]
        subj_text = subj_text[0].upper() + subj_text[1:]
        text = f"{subj_text} was exactly {offset} {unit}{plural} above {catA.items[ib]}."
        atoms = [("relative", catA.name, ia, catA.name, ib, offset)]
        return Clue("relative", text, atoms)

    def gen_compound(self, n_children: int = 2) -> Clue:
        children = []
        seen = set()
        tries = 0
        while len(children) < n_children and tries < 20:
            tries += 1
            c = self.gen_direct(positive=True)
            key = frozenset(c.atoms)
            if key in seen:
                continue
            seen.add(key)
            children.append(c)
        text = "All of these are true: " + " ".join(c.text for c in children)
        atoms = [a for c in children for a in c.atoms]
        return Clue("compound", text, atoms)

    def gen_clue(self, profile: Dict[str, float]) -> Optional[Clue]:
        """profile: weights for 'positive','negative','either_or','relative','compound'."""
        kinds, weights = zip(*profile.items())
        kind = self.rng.choices(kinds, weights=weights, k=1)[0]
        if kind == "positive":
            return self.gen_direct(True)
        if kind == "negative":
            return self.gen_direct(False)
        if kind == "either_or":
            return self.gen_either_or()
        if kind == "relative":
            return self.gen_relative() or self.gen_direct(False)
        if kind == "compound":
            return self.gen_compound()
        raise ValueError(kind)

    # -- solver (pure propagation, no branching) -----------------------------
    def _new_possible(self) -> Dict[Tuple[str, int], Set[int]]:
        return {(c.name, i): set(range(self.N)) for c in self.categories for i in range(self.N)}

    def _propagate(self, atoms_list: List[Tuple]) -> Tuple[Dict[Tuple[str, int], Set[int]], bool, int]:
        possible = self._new_possible()
        # fix the anchor category immediately (by construction, item i -> slot i)
        for i in range(self.N):
            possible[(self.anchor_cat.name, i)] = {i}

        positives, negatives, relatives = [], [], []
        for kind, catA, ia, catB, ib, offset in atoms_list:
            if kind == "positive":
                positives.append((catA, ia, catB, ib))
            elif kind == "negative":
                negatives.append((catA, ia, catB, ib))
            elif kind == "relative":
                relatives.append((catA, ia, catB, ib, offset))

        changed = True
        rounds = 0
        while changed:
            changed = False
            rounds += 1
            # positives: intersect
            for catA, ia, catB, ib in positives:
                inter = possible[(catA, ia)] & possible[(catB, ib)]
                if inter != possible[(catA, ia)]:
                    possible[(catA, ia)] = set(inter); changed = True
                if inter != possible[(catB, ib)]:
                    possible[(catB, ib)] = set(inter); changed = True
            # relatives: sb = sa - offset
            for catA, ia, catB, ib, offset in relatives:
                allowed_a = {s for s in possible[(catA, ia)]
                             if (s - offset) in possible[(catB, ib)]}
                allowed_b = {s for s in possible[(catB, ib)]
                             if (s + offset) in possible[(catA, ia)]}
                if allowed_a != possible[(catA, ia)]:
                    possible[(catA, ia)] = allowed_a; changed = True
                if allowed_b != possible[(catB, ib)]:
                    possible[(catB, ib)] = allowed_b; changed = True
            # negatives: if one side is singleton, remove that slot from the other
            for catA, ia, catB, ib in negatives:
                pa, pb = possible[(catA, ia)], possible[(catB, ib)]
                if len(pb) == 1:
                    s = next(iter(pb))
                    if s in pa:
                        pa.discard(s); changed = True
                if len(pa) == 1:
                    s = next(iter(pa))
                    if s in pb:
                        pb.discard(s); changed = True
            # Latin-square rule: within each category, a slot claimed by one
            # item (singleton) can't belong to any other item in that category
            for c in self.categories:
                singles = {}
                for i in range(self.N):
                    p = possible[(c.name, i)]
                    if len(p) == 1:
                        singles[i] = next(iter(p))
                for i in range(self.N):
                    if i in singles:
                        continue
                    p = possible[(c.name, i)]
                    new_p = p - set(singles.values())
                    if new_p != p:
                        possible[(c.name, i)] = new_p; changed = True

        solved = all(len(possible[(c.name, i)]) == 1
                     for c in self.categories for i in range(self.N))
        consistent = all(len(possible[k]) > 0 for k in possible)
        return possible, (solved and consistent), rounds

    def is_pure_deduction_solvable(self, clues: List[Clue]) -> bool:
        atoms = [a for cl in clues for a in cl.atoms]
        _, solved, _ = self._propagate(atoms)
        return solved

    def deduction_depth(self, clues: List[Clue]) -> int:
        """Number of propagation rounds needed to fully solve -- an objective
        proxy for how many chained inference steps a solver needs, independent
        of which clue-type mix produced the puzzle."""
        atoms = [a for cl in clues for a in cl.atoms]
        _, solved, rounds = self._propagate(atoms)
        return rounds if solved else -1

    # -- puzzle assembly ------------------------------------------------------
    def build_puzzle(self, profile: Dict[str, float], max_clues: int = 30,
                      min_clues: int = 6, max_attempts: int = 500,
                      min_depth: int = 0) -> List[Clue]:
        """Add clues one at a time (profile-weighted) until pure propagation
        solves the grid, then greedily strip redundant clues -- sparser
        clue sets generally require MORE deduction rounds, not fewer, so
        min_depth is enforced as a floor during stripping (don't strip past
        the point where depth would drop below it), not during adding."""
        clues: List[Clue] = []
        seen_atom_sets = set()
        seen_atoms = set()  # individual atoms, catches duplicates hidden inside compound clues
        attempts = 0

        def solved_and_depth(cl):
            atoms = [a for c in cl for a in c.atoms]
            _, ok, rounds = self._propagate(atoms)
            return ok, rounds

        while not self.is_pure_deduction_solvable(clues):
            if attempts > max_attempts:
                raise RuntimeError("Could not reach a pure-deduction solution "
                                    "within max_attempts -- widen profile, raise "
                                    "max_attempts, or raise max_clues")
            attempts += 1
            c = self.gen_clue(profile)
            key = frozenset(c.atoms)
            if key in seen_atom_sets:
                continue
            # reject if ANY individual atom (including one nested inside a
            # compound clue) duplicates a fact already asserted elsewhere
            if any(a in seen_atoms for a in c.atoms):
                continue
            seen_atom_sets.add(key)
            seen_atoms.update(c.atoms)
            clues.append(c)

        # strip redundant clues (keep order stable, re-check each removal),
        # but never strip below the required min_depth
        i = 0
        while i < len(clues) and len(clues) > min_clues:
            trial = clues[:i] + clues[i + 1:]
            ok, depth = solved_and_depth(trial)
            if ok and depth >= min_depth:
                clues = trial
            else:
                i += 1
        self.rng.shuffle(clues)
        return clues


# ─────────────────────────────────────────────────────────────────────────
# Difficulty profiles
# ─────────────────────────────────────────────────────────────────────────
PROFILES = {
    "easy":   {"positive": 0.55, "negative": 0.35, "either_or": 0.10, "relative": 0.0, "compound": 0.0},
    "medium": {"positive": 0.35, "negative": 0.35, "either_or": 0.20, "relative": 0.10, "compound": 0.0},
    "hard":   {"positive": 0.15, "negative": 0.35, "either_or": 0.25, "relative": 0.20, "compound": 0.05},
    "expert": {"positive": 0.10, "negative": 0.30, "either_or": 0.25, "relative": 0.25, "compound": 0.10},
}

# Minimum propagation rounds required for a puzzle to count as that
# difficulty -- measured, not assumed (see build_volume validation).
# Ensures Expert is provably harder than Hard, not just differently flavored.
DEPTH_FLOORS = {"easy": 0, "medium": 6, "hard": 7, "expert": 9}
