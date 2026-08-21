"""
theme_alaska_test.py
─────────────────────────────────────────────────────────────────────────────
Minimal test build of the Alaska cruise mystery theme -- Mix-up puzzle type
only, small word banks, just to prove the pipeline (theme -> engine ->
solver -> clue text) works end-to-end for cruise content before we build
out the full category bank and the Participation puzzle type.
"""

from themes import ScenarioTheme, ThemeCategory, build_themed_puzzle
from puzzle_engine import PROFILES

ALASKA_MIXUP_TEST = ScenarioTheme(
    name="Alaska Cruise Mix-Up (test)",
    title_patterns=["The {noun} Mix-Up", "The Case of the {noun}"],
    title_nouns=["Missing Sunglasses", "Mixed-Up Luggage", "Misplaced Camera",
                 "Wandering Umbrella", "Swapped Jacket"],
    intro_openers=[
        "As the ship cruised toward Alaska",
        "Somewhere between Ketchikan and Juneau",
        "As the purser's desk filled with lost-and-found reports",
    ],
    intro_template="{opener}, something had gone missing. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Passenger", "person", pool=[
            "Maren", "Carl", "Ruth", "Dale", "Bev", "Wyatt", "Joan",
            "Hank", "Peg", "Miles", "Dot", "Rex",
        ]),
        ThemeCategory("Port", "attribute", verb="was ashore at", pool=[
            "Ketchikan", "Juneau", "Skagway", "Sitka", "Icy Strait Point",
        ]),
        ThemeCategory("Item", "attribute", verb="lost", possessive="their", pool=[
            "sunglasses", "room key card", "luggage tag", "excursion ticket",
            "umbrella", "camera",
        ]),
        ThemeCategory("Time", "attribute", verb="reported it", pool=[
            "at breakfast", "mid-morning", "at lunch", "in the afternoon",
            "at dinner", "late at night",
        ]),
        ThemeCategory("Deck", "ordinal", unit="deck", pool=[]),
    ],
)

if __name__ == "__main__":
    N = 5
    for difficulty in ["easy", "medium", "hard", "expert"]:
        result = build_themed_puzzle(ALASKA_MIXUP_TEST, N=N, profile_name=difficulty, seed=42)
        print(f"\n{'='*70}\n{difficulty.upper()}  —  {result['title']}\n{'='*70}")
        print(result["intro"])
        print(f"\nCategories:")
        for cat, items in result["categories"].items():
            print(f"  {cat}: {items}")
        print(f"\nClues ({result['n_clues']}):")
        for i, c in enumerate(result["clues"], 1):
            print(f"  {i}. {c}")
        print(f"\nSolution: {result['solution']}")
        print(f"Deduction depth: {result['deduction_depth']}  |  Direct fraction: {result['direct_fraction']}")
