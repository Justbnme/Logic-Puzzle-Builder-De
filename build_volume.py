"""
build_volume.py
─────────────────────────────────────────────────────────────────────────────
Generates a full Master Logic volume: 50 Hard + 50 Expert puzzles, N=7,
4 categories, rotating through all 19 themes. Outputs structured JSON
(one record per puzzle) plus a summary report for review before rendering.
"""

import json
import random
from themes import THEMES, build_themed_puzzle
from verify_unique import verify_puzzle_unique

N = 7
K = 4  # categories per puzzle (Person + 2 attributes + 1 ordinal)


def build_volume(volume_number: int, n_hard: int = 50, n_expert: int = 50,
                  base_seed: int = 1000, verify: bool = True) -> list:
    rng = random.Random(base_seed + volume_number)
    theme_keys = list(THEMES.keys())

    # shuffled rotation order, reshuffled each time we exhaust the list,
    # so no theme repeats until every other theme has had a turn
    def theme_cycle():
        while True:
            order = theme_keys[:]
            rng.shuffle(order)
            for k in order:
                yield k

    cycle = theme_cycle()
    theme_instance_count = {k: 0 for k in theme_keys}

    puzzles = []
    plan = [("hard", i + 1) for i in range(n_hard)] + [("expert", i + 1) for i in range(n_expert)]
    for idx, (difficulty, num_in_book) in enumerate(plan, start=1):
        theme_key = next(cycle)
        theme_instance_count[theme_key] += 1
        instance_num = theme_instance_count[theme_key]
        seed = base_seed + volume_number * 100000 + idx * 37
        p = build_themed_puzzle(THEMES[theme_key], N, difficulty, seed=seed,
                                 puzzle_number=instance_num)
        p["puzzle_index"] = idx
        p["difficulty"] = difficulty
        p["theme_key"] = theme_key

        if verify:
            engine = p.pop("_engine")
            clues = p.pop("_clues_raw")
            cat_names = list(p["categories"].keys())
            report = verify_puzzle_unique(cat_names, N, engine.anchor_cat.name, clues)
            p["unique_solution"] = report["unique"]
            p["n_solutions_found"] = report["n_solutions_found"]
        else:
            p.pop("_engine", None)
            p.pop("_clues_raw", None)

        puzzles.append(p)
    return puzzles


def report(puzzles: list):
    titles = [p["title"] for p in puzzles]
    dupes = {t for t in titles if titles.count(t) > 1}
    theme_counts = {}
    clue_counts = []
    for p in puzzles:
        theme_counts[p["theme_key"]] = theme_counts.get(p["theme_key"], 0) + 1
        clue_counts.append(p["n_clues"])
    print(f"Total puzzles: {len(puzzles)}")
    print(f"Hard: {sum(1 for p in puzzles if p['difficulty']=='hard')}, "
          f"Expert: {sum(1 for p in puzzles if p['difficulty']=='expert')}")
    print(f"Duplicate titles: {len(dupes)} {'-> ' + str(dupes) if dupes else ''}")
    print(f"Clue count range: {min(clue_counts)}-{max(clue_counts)}, "
          f"avg {sum(clue_counts)/len(clue_counts):.1f}")
    print("Theme distribution:")
    for k, v in sorted(theme_counts.items(), key=lambda x: -x[1]):
        print(f"  {k:22s} {v}")
    # verify no two consecutive puzzles share a theme
    consec = sum(1 for i in range(1, len(puzzles))
                 if puzzles[i]["theme_key"] == puzzles[i - 1]["theme_key"])
    print(f"Consecutive same-theme repeats: {consec}")
    if "unique_solution" in puzzles[0]:
        non_unique = [p["puzzle_index"] for p in puzzles if not p["unique_solution"]]
        print(f"Non-unique solutions (independent brute-force check): {len(non_unique)} {non_unique if non_unique else ''}")


if __name__ == "__main__":
    puzzles = build_volume(volume_number=1)
    report(puzzles)
    with open("master_logic_vol1.json", "w") as f:
        json.dump(puzzles, f, indent=1)
    print("\nSaved master_logic_vol1.json")
