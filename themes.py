"""
themes.py
─────────────────────────────────────────────────────────────────────────────
Scenario layer on top of puzzle_engine.py. A ScenarioTheme defines a
narrative setting (word banks per category, title patterns, intro text) --
build_themed_puzzle() samples N items per category from the theme's pools,
builds a real puzzle via PuzzleEngine, and returns everything needed to
lay out a page: title, intro, category dict (for the grid), and clues.

Word-bank pools are intentionally larger than any single puzzle's N, so
running the same theme repeatedly (e.g. 50 Hard + 50 Expert puzzles in one
book) produces different item combinations each time rather than reusing
the same fixed set puzzle after puzzle.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Optional
from puzzle_engine import Category, PuzzleEngine, PROFILES


@dataclass
class ThemeCategory:
    name: str
    kind: str            # "person" | "ordinal" | "attribute"
    pool: List[str]       # word bank -- must be >= max N you'll ever draw
    verb: str = "had"     # only used for kind="attribute"
    unit: Optional[str] = None  # only used for kind="ordinal"


@dataclass
class ScenarioTheme:
    name: str
    title_patterns: List[str]     # e.g. ["The {noun} Affair"] -- {noun} drawn from title_nouns
    title_nouns: List[str]
    intro_template: str            # "{opening} ... Use the clues to match each {subject} to their {axes}."
    intro_openers: List[str]
    categories: List[ThemeCategory]  # first one should be kind="person"


def build_themed_puzzle(theme: ScenarioTheme, N: int, profile_name: str,
                         seed: int, puzzle_number: int = 1) -> dict:
    rng = random.Random(seed)

    engine_cats = []
    for tc in theme.categories:
        if tc.kind != "ordinal" and len(tc.pool) < N:
            raise ValueError(f"{theme.name}/{tc.name}: pool has {len(tc.pool)} items, need >= {N}")
        if tc.kind == "ordinal":
            chosen = [str(i + 1) for i in range(N)]
        else:
            chosen = rng.sample(tc.pool, N)
        cat = Category(tc.name, chosen, ordinal=(tc.kind == "ordinal"),
                        kind=tc.kind, verb=tc.verb, unit=tc.unit)
        engine_cats.append(cat)

    engine = PuzzleEngine(engine_cats, seed=seed)
    clues = engine.build_puzzle(PROFILES[profile_name], max_clues=30, min_clues=6)

    noun = rng.choice(theme.title_nouns)
    pattern = rng.choice(theme.title_patterns)
    title = pattern.format(noun=noun) + f" {puzzle_number}"

    opener = rng.choice(theme.intro_openers)
    person_cat = theme.categories[0]
    other_axes = ", ".join(c.name.lower() for c in theme.categories[1:-1]) + \
                 f", and {theme.categories[-1].name.lower()}"
    intro = theme.intro_template.format(opener=opener, subject=person_cat.name.lower(),
                                          axes=other_axes)

    return {
        "title": title,
        "intro": intro,
        "categories": {c.name: c.items for c in engine_cats},
        "clues": [c.text for c in clues],
        "solution": engine.solution,
        "n_clues": len(clues),
    }


# ─────────────────────────────────────────────────────────────────────────
# Sample themes (placeholder word banks -- swap in your own before print)
# ─────────────────────────────────────────────────────────────────────────

MANOR_MYSTERY = ScenarioTheme(
    name="Manor Mystery",
    title_patterns=["The {noun} Affair", "The Case of the {noun}"],
    title_nouns=["Locked Study", "Missing Brooch", "Silent Parlor", "Hidden Ledger",
                 "Vanished Heir", "Curious Will", "Midnight Caller", "Forgotten Key"],
    intro_openers=[
        "When the lights flickered at the estate",
        "As the storm rolled in over the manor",
        "Before the reading of the will began",
        "While the guests gathered for dinner",
    ],
    intro_template="{opener}, each {subject} had a story to tell. "
                    "The clues below will reveal each {subject}'s {axes}.",
    categories=[
        ThemeCategory("Guest", "person", pool=[
            "the Envoy", "the Curator", "the Heiress", "the Professor", "the Major",
            "the Actress", "the Doctor", "the Widow", "the Butler", "the Colonel",
            "the Journalist", "the Solicitor",
        ]),
        ThemeCategory("Coat", "attribute", verb="wore", pool=[
            "a grey coat", "a navy coat", "an ivory coat", "a camel coat", "a plum coat",
            "a russet coat", "a charcoal coat", "a forest coat", "a burgundy coat", "a slate coat",
        ]),
        ThemeCategory("Drink", "attribute", verb="was holding", pool=[
            "a cordial", "a soda water", "a brandy", "a coffee", "a claret",
            "a champagne", "a chamomile tea", "a sherry", "a whisky", "a lemonade",
        ]),
        ThemeCategory("Floor", "ordinal", unit="floor", pool=[]),  # filled 1..N automatically
    ],
)

TRACK_MEET = ScenarioTheme(
    name="Track Meet",
    title_patterns=["The {noun} Track Meet", "The {noun} Relay"],
    title_nouns=["Summer", "District", "Regional", "Autumn", "Downtown", "Riverside", "County"],
    intro_openers=[
        "Under the stadium lights", "As the starting gun echoed",
        "With the crowd on its feet", "As the final heat approached",
    ],
    intro_template="{opener}, the meet got under way. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Runner", "person", pool=[
            "Indira", "Holt", "Cyra", "Marsh", "Kerr", "Priya", "Ronan",
            "Delia", "Soren", "Talia", "Wren", "Amos",
        ]),
        ThemeCategory("Spikes", "attribute", verb="laced up", pool=[
            "red spikes", "yellow spikes", "pink spikes", "silver spikes", "green spikes",
            "blue spikes", "orange spikes", "white spikes", "black spikes", "gold spikes",
        ]),
        ThemeCategory("Vest", "attribute", verb="wore", pool=[
            "a white vest", "an orange vest", "a red vest", "a black vest", "a gold vest",
            "a navy vest", "a teal vest", "a purple vest", "a maroon vest", "a lime vest",
        ]),
        ThemeCategory("Place", "ordinal", unit="place", pool=[]),
    ],
)

THEMES = {"manor_mystery": MANOR_MYSTERY, "track_meet": TRACK_MEET}
