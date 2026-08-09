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
from puzzle_engine import Category, PuzzleEngine, PROFILES, DEPTH_FLOORS


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
        "deduction_depth": engine.deduction_depth(clues),
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

WINE_TASTING = ScenarioTheme(
    name="Wine Tasting",
    title_patterns=["The {noun} Tasting", "The {noun} Cellar"],
    title_nouns=["Vineyard", "Harvest", "Reserve", "Estate", "Cellar", "Blind", "Autumn"],
    intro_openers=["As the corks were pulled", "Before the final pour", "As the sommelier circled the table"],
    intro_template="{opener}, seven glasses waited to be judged. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Taster", "person", pool=[
            "Odette", "Marcus", "Ines", "Callum", "Bea", "Rafael", "Noor",
            "Sylvie", "Dax", "Petra", "Owen", "Liana",
        ]),
        ThemeCategory("Varietal", "attribute", verb="poured", pool=[
            "a Merlot", "a Malbec", "a Riesling", "a Chardonnay", "a Syrah",
            "a Pinot Noir", "a Sauvignon Blanc", "a Tempranillo", "a Grenache", "a Viognier",
        ]),
        ThemeCategory("Region", "attribute", verb="favored", pool=[
            "a Napa selection", "a Tuscan selection", "a Rioja selection", "a Mosel selection",
            "a Barossa selection", "a Loire selection", "a Douro selection", "a Marlborough selection",
            "a Piedmont selection", "a Stellenbosch selection",
        ]),
        ThemeCategory("Flight", "ordinal", unit="flight", pool=[]),
    ],
)

BAKE_OFF = ScenarioTheme(
    name="Bake-Off",
    title_patterns=["The {noun} Bake-Off", "The {noun} Bake Tent"],
    title_nouns=["Village", "Summer", "County", "Blue Ribbon", "Harvest", "Weekend"],
    intro_openers=["As the ovens cooled", "Under the striped tent", "With flour still on every apron"],
    intro_template="{opener}, the judges took their seats. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Baker", "person", pool=[
            "Hazel", "Tobias", "Junie", "Mateo", "Rosalind", "Faisal", "Della",
            "Pascal", "Winnie", "Idris", "Coral", "Beckett",
        ]),
        ThemeCategory("Pastry", "attribute", verb="entered", pool=[
            "a lemon tart", "a sourdough loaf", "a chocolate torte", "a fruit galette",
            "a custard pie", "a spice cake", "a puff pastry", "a berry crumble",
            "a cheese souffle", "a caramel roll",
        ]),
        ThemeCategory("Apron", "attribute", verb="wore", pool=[
            "a striped apron", "a floral apron", "a denim apron", "a gingham apron",
            "a canvas apron", "a polka-dot apron", "a linen apron", "a checkered apron",
            "a solid red apron", "a mustard apron",
        ]),
        ThemeCategory("Table", "ordinal", unit="table", pool=[]),
    ],
)

CHESS_OPEN = ScenarioTheme(
    name="Chess Open",
    title_patterns=["The {noun} Open", "The {noun} Chess Championship"],
    title_nouns=["Winter", "Capital City", "Invitational", "Weekend", "Regional", "Masters"],
    intro_openers=["As the clocks were set", "With the halls quiet", "As the final round approached"],
    intro_template="{opener}, seven players sat down to play. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Player", "person", pool=[
            "Anders", "Yumi", "Grant", "Simone", "Tobin", "Aiko", "Declan",
            "Marguerite", "Felix", "Nadia", "Otis", "Junko",
        ]),
        ThemeCategory("Opening", "attribute", verb="played", pool=[
            "the Sicilian Defense", "the Queen's Gambit", "the Ruy Lopez", "the King's Indian",
            "the French Defense", "the English Opening", "the Caro-Kann", "the Nimzo-Indian",
            "the Scandinavian Defense", "the Grunfeld Defense",
        ]),
        ThemeCategory("Club", "attribute", verb="represented", pool=[
            "the Riverside Club", "the Downtown Club", "the University Club", "the Harborview Club",
            "the Lakeside Club", "the Ashford Club", "the Meridian Club", "the Old Town Club",
            "the Brookline Club", "the Foxwood Club",
        ]),
        ThemeCategory("Board", "ordinal", unit="board", pool=[]),
    ],
)

GALLERY_OPENING = ScenarioTheme(
    name="Gallery Opening",
    title_patterns=["The {noun} Opening", "The {noun} Exhibit"],
    title_nouns=["Silent", "Midnight", "Debut", "Private", "Spring", "Uptown"],
    intro_openers=["As the doors opened", "Under the gallery lights", "As the wine glasses filled"],
    intro_template="{opener}, seven artists waited for the crowd. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Artist", "person", pool=[
            "Imre", "Solange", "Kato", "Perpetua", "Nils", "Adaeze", "Ronan",
            "Yara", "Bastien", "Mireille", "Theo", "Odalys",
        ]),
        ThemeCategory("Medium", "attribute", verb="worked in", pool=[
            "oil paint", "charcoal", "watercolor", "bronze sculpture", "mixed media",
            "ink wash", "pastel", "collage", "clay", "etching",
        ]),
        ThemeCategory("Palette", "attribute", verb="favored", pool=[
            "a monochrome palette", "an earth-tone palette", "a jewel-tone palette",
            "a pastel palette", "a stark black-and-white palette", "a warm palette",
            "a cool palette", "a metallic palette", "a muted palette", "a neon palette",
        ]),
        ThemeCategory("Wall", "ordinal", unit="wall", pool=[]),
    ],
)

CRUISE_MYSTERY = ScenarioTheme(
    name="Cruise Mystery",
    title_patterns=["The {noun} Voyage", "The {noun} Crossing"],
    title_nouns=["Midnight", "Moonlit", "Vanishing", "Silent", "Foggy", "Final"],
    intro_openers=["As the ship left port", "Under a starless sky", "As the engines slowed at midnight"],
    intro_template="{opener}, seven passengers had a story to tell. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Passenger", "person", pool=[
            "the Captain's Guest", "the Steward", "the Violinist", "the Widower", "the Diplomat",
            "the Nurse", "the Gambler", "the Chef", "the Photographer", "the Tutor",
            "the Botanist", "the Reporter",
        ]),
        ThemeCategory("Excursion", "attribute", verb="booked", pool=[
            "a snorkeling excursion", "a walking tour", "a fishing charter", "a museum visit",
            "a cooking class", "a horseback ride", "a wine tour", "a kayak trip",
            "a zip-line tour", "a market tour",
        ]),
        ThemeCategory("Cocktail", "attribute", verb="ordered", pool=[
            "a mai tai", "a martini", "a mojito", "a spritz", "a daiquiri",
            "a negroni", "a rum punch", "a gin fizz", "a sidecar", "a paloma",
        ]),
        ThemeCategory("Deck", "ordinal", unit="deck", pool=[]),
    ],
)

FILM_FESTIVAL = ScenarioTheme(
    name="Film Festival",
    title_patterns=["The {noun} Film Festival", "The {noun} Screening"],
    title_nouns=["Independent", "Midnight", "International", "Coastal", "Autumn", "Debut"],
    intro_openers=["As the red carpet rolled out", "Under the marquee lights", "As the projectors warmed up"],
    intro_template="{opener}, seven directors waited for their reviews. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Director", "person", pool=[
            "Wren", "Achille", "Noor", "Casimir", "Bijou", "Halston", "Perpetua",
            "Idris", "Solveig", "Marchetti", "Anouk", "Osei",
        ]),
        ThemeCategory("Genre", "attribute", verb="screened", pool=[
            "a documentary", "a period drama", "a psychological thriller", "a satire",
            "a coming-of-age film", "a war epic", "a noir mystery", "an animated feature",
            "a road movie", "a courtroom drama",
        ]),
        ThemeCategory("Award", "attribute", verb="won", pool=[
            "the Audience Award", "the Jury Prize", "Best Screenplay", "Best Director",
            "the Critics' Choice", "Best Ensemble", "the Discovery Award", "Best Score",
            "the Golden Reel", "Best Cinematography",
        ]),
        ThemeCategory("Theater", "ordinal", unit="theater", pool=[]),
    ],
)

SPELLING_BEE = ScenarioTheme(
    name="Spelling Bee",
    title_patterns=["The {noun} Spelling Bee", "The {noun} Bee"],
    title_nouns=["Regional", "County", "Citywide", "Autumn", "Championship", "Junior"],
    intro_openers=["As the microphone crackled on", "With the audience hushed", "As the final round began"],
    intro_template="{opener}, seven contestants stepped up in turn. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Contestant", "person", pool=[
            "Beatrix", "Emmett", "Zora", "Gideon", "Marisol", "Tobias", "Wren",
            "Achebe", "Junie", "Rosalind", "Kellan", "Odalys",
        ]),
        ThemeCategory("Word", "attribute", verb="was given", pool=[
            "a science word", "a geography word", "a history word", "a French loanword",
            "a Latin root word", "a music term", "a nature word", "an architecture term",
            "a legal term", "a medical term",
        ]),
        ThemeCategory("School", "attribute", verb="represented", pool=[
            "Ashford Elementary", "Brookline Academy", "Cedar Ridge School", "Dunmore Prep",
            "Elmwood School", "Fairview Academy", "Glenhaven School", "Harborview Elementary",
            "Ivy Lane School", "Juniper Academy",
        ]),
        ThemeCategory("Round", "ordinal", unit="round", pool=[]),
    ],
)

ANTIQUE_AUCTION = ScenarioTheme(
    name="Antique Auction",
    title_patterns=["The {noun} Auction", "The {noun} Estate Sale"],
    title_nouns=["Midnight", "Estate", "Silent", "Private", "Riverside", "Autumn"],
    intro_openers=["As the gavel was raised", "Under the auction lights", "As the final lot was called"],
    intro_template="{opener}, seven bidders raised their paddles. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Bidder", "person", pool=[
            "the Antiquarian", "the Collector", "the Dealer", "the Heiress", "the Appraiser",
            "the Retiree", "the Investor", "the Decorator", "the Historian", "the Broker",
            "the Widow", "the Curator",
        ]),
        ThemeCategory("Item", "attribute", verb="won", pool=[
            "a silver tea set", "a grandfather clock", "a porcelain vase", "an oil portrait",
            "a mahogany desk", "a jeweled brooch", "a bronze statue", "a leather-bound atlas",
            "a crystal chandelier", "a carved chess set",
        ]),
        ThemeCategory("Paddle", "attribute", verb="carried", pool=[
            "a red paddle", "a blue paddle", "a green paddle", "a yellow paddle",
            "a white paddle", "a black paddle", "a purple paddle", "an orange paddle",
            "a silver paddle", "a gold paddle",
        ]),
        ThemeCategory("Row", "ordinal", unit="row", pool=[]),
    ],
)

JAZZ_CLUB = ScenarioTheme(
    name="Jazz Club",
    title_patterns=["The {noun} Set", "The {noun} Jazz Night"],
    title_nouns=["Late Night", "Blue Room", "Basement", "Sunday", "Uptown", "Encore"],
    intro_openers=["As the lights dimmed", "As the bass player counted in", "Under the smoky stage lights"],
    intro_template="{opener}, seven musicians took the stage in turn. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Musician", "person", pool=[
            "Delphine", "Roscoe", "Ines", "Marcus", "Coretta", "Django", "Odette",
            "Silas", "Yolanda", "Booker", "Vashti", "Elmore",
        ]),
        ThemeCategory("Instrument", "attribute", verb="played", pool=[
            "the trumpet", "the upright bass", "the saxophone", "the piano",
            "the clarinet", "the trombone", "the drums", "the vibraphone",
            "the flute", "the guitar",
        ]),
        ThemeCategory("Theme", "attribute", verb="opened with", pool=[
            "a blues set", "a bebop set", "a ballad set", "a swing set",
            "a Latin jazz set", "a fusion set", "a standards set", "a modal set",
            "a big band set", "an original composition set",
        ]),
        ThemeCategory("Set", "ordinal", unit="set", pool=[]),
    ],
)

GARDEN_SHOW = ScenarioTheme(
    name="Garden Show",
    title_patterns=["The {noun} Garden Show", "The {noun} Flower Show"],
    title_nouns=["Spring", "County", "Rose", "Botanical", "Annual", "Blue Ribbon"],
    intro_openers=["As the judging began", "Under the striped tents", "As the morning dew dried"],
    intro_template="{opener}, seven exhibitors waited for the ribbons. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Exhibitor", "person", pool=[
            "Marigold", "Elston", "Petra", "Auggie", "Rosamund", "Fennimore", "Iolanthe",
            "Basil", "Verbena", "Clover", "Thistle", "Linden",
        ]),
        ThemeCategory("Flower", "attribute", verb="entered", pool=[
            "a peony", "a dahlia", "an orchid", "a hydrangea", "a rose",
            "a tulip", "a chrysanthemum", "a delphinium", "a zinnia", "a foxglove",
        ]),
        ThemeCategory("Ribbon", "attribute", verb="was awarded", pool=[
            "a blue ribbon", "a red ribbon", "a yellow ribbon", "a white ribbon",
            "a green ribbon", "a purple ribbon", "a rosette ribbon", "a gold ribbon",
            "a silver ribbon", "a bronze ribbon",
        ]),
        ThemeCategory("Tent", "ordinal", unit="tent", pool=[]),
    ],
)

REGATTA = ScenarioTheme(
    name="Regatta",
    title_patterns=["The {noun} Regatta", "The {noun} Race"],
    title_nouns=["Harbor", "Summer", "Coastal", "Invitational", "Cup", "Bay"],
    intro_openers=["As the starting flag dropped", "Under a clear morning sky", "As the boats lined up"],
    intro_template="{opener}, seven sailors made ready. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Sailor", "person", pool=[
            "Merit", "Torsten", "Amara", "Callan", "Seraphine", "Bowen", "Isolde",
            "Fenwick", "Dagny", "Corwin", "Marisela", "Osric",
        ]),
        ThemeCategory("Boat", "attribute", verb="sailed", pool=[
            "the Wavecrest", "the Storm Petrel", "the Blue Heron", "the Northern Star",
            "the Sea Fox", "the Windrunner", "the Coral Queen", "the Tidewater",
            "the Halcyon", "the Meridian",
        ]),
        ThemeCategory("Sponsor", "attribute", verb="was sponsored by", pool=[
            "the Harbor Club", "the Marina Grill", "a local bank", "a boatyard",
            "a sailing school", "a coastal brewery", "a yacht broker", "a local paper",
            "a marine supply shop", "a rigging company",
        ]),
        ThemeCategory("Lane", "ordinal", unit="lane", pool=[]),
    ],
)

COOKING_COMPETITION = ScenarioTheme(
    name="Cooking Competition",
    title_patterns=["The {noun} Cook-Off", "The {noun} Kitchen Challenge"],
    title_nouns=["Iron Skillet", "Weekend", "Regional", "Chef's Table", "Harvest", "Fire & Ice"],
    intro_openers=["As the timers were set", "Under the heat lamps", "As the judges took their seats"],
    intro_template="{opener}, seven chefs plated their dishes. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Chef", "person", pool=[
            "Basil", "Saffron", "Remy", "Juniper", "Cayenne", "Rosemary", "Thane",
            "Clove", "Sorrel", "Anise", "Marjoram", "Tarragon",
        ]),
        ThemeCategory("Dish", "attribute", verb="plated", pool=[
            "a seared duck breast", "a wild mushroom risotto", "a braised short rib",
            "a citrus-glazed salmon", "a roasted root vegetable tart", "a lobster bisque",
            "a smoked brisket", "a saffron paella", "a wild rice pilaf", "a stuffed quail",
        ]),
        ThemeCategory("Apron", "attribute", verb="wore", pool=[
            "a black apron", "a white apron", "a red apron", "a striped apron",
            "a chef's coat", "a bib apron", "a waxed canvas apron", "a monogrammed apron",
            "a leather apron", "a linen apron",
        ]),
        ThemeCategory("Station", "ordinal", unit="station", pool=[]),
    ],
)

POETRY_SLAM = ScenarioTheme(
    name="Poetry Slam",
    title_patterns=["The {noun} Slam", "The {noun} Open Mic"],
    title_nouns=["Midnight", "Downtown", "Open", "Underground", "Sunday", "Encore"],
    intro_openers=["As the mic was passed", "Under the low stage lights", "As the crowd fell silent"],
    intro_template="{opener}, seven poets took their turn. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Poet", "person", pool=[
            "Lior", "Amani", "Gideon", "Xochitl", "Elowen", "Barnaby", "Suri",
            "Casper", "Naledi", "Rune", "Adaora", "Finch",
        ]),
        ThemeCategory("Subject", "attribute", verb="wrote about", pool=[
            "heartbreak", "the city at night", "family history", "the ocean",
            "grief", "hope", "childhood", "protest", "memory", "distance",
        ]),
        ThemeCategory("Hometown", "attribute", verb="came from", pool=[
            "Ashford", "Brookline", "Cedar Falls", "Dunmore", "Elmwood",
            "Fairview", "Glenhaven", "Harborview", "Ivy Lane", "Juniper Hill",
        ]),
        ThemeCategory("Slot", "ordinal", unit="slot", pool=[]),
    ],
)

SCIENCE_FAIR = ScenarioTheme(
    name="Science Fair",
    title_patterns=["The {noun} Science Fair", "The {noun} Expo"],
    title_nouns=["Regional", "Districtwide", "Spring", "Junior", "STEM", "Innovation"],
    intro_openers=["As the judges began their rounds", "Under the gymnasium lights", "As the last poster went up"],
    intro_template="{opener}, seven students stood by their projects. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Student", "person", pool=[
            "Priya", "Emeka", "Louisa", "Tobin", "Anouk", "Desmond", "Kiri",
            "Osei", "Wren", "Achebe", "Marisol", "Beckett",
        ]),
        ThemeCategory("Project", "attribute", verb="presented", pool=[
            "a robotics project", "a plant genetics project", "a solar energy project",
            "a water filtration project", "an earthquake simulator", "a memory-testing app",
            "a weather balloon project", "a bacteria growth project", "a wind turbine model",
            "an ocean acidity project",
        ]),
        ThemeCategory("School", "attribute", verb="represented", pool=[
            "Ashford Middle School", "Brookline Academy", "Cedar Ridge School", "Dunmore Prep",
            "Elmwood School", "Fairview Academy", "Glenhaven School", "Harborview Middle School",
            "Ivy Lane School", "Juniper Academy",
        ]),
        ThemeCategory("Table", "ordinal", unit="table", pool=[]),
    ],
)

VINTAGE_CAR_SHOW = ScenarioTheme(
    name="Vintage Car Show",
    title_patterns=["The {noun} Car Show", "The {noun} Cruise-In"],
    title_nouns=["Summer", "Downtown", "Classic", "Chrome & Steel", "Sunday", "County"],
    intro_openers=["As the engines idled down", "Under the afternoon sun", "As the judges walked the rows"],
    intro_template="{opener}, seven owners polished their chrome. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Owner", "person", pool=[
            "Duke", "Marlowe", "Etta", "Roscoe", "Dot", "Chester", "Vivian",
            "Gus", "Loretta", "Hank", "Corrine", "Boyd",
        ]),
        ThemeCategory("Car", "attribute", verb="brought", pool=[
            "a '57 Bel Air", "a '65 Mustang", "a '69 Camaro", "a '58 Corvette",
            "a '72 Charger", "a '63 Thunderbird", "a '67 GTO", "a '55 Beetle",
            "a '70 Challenger", "a '62 Impala",
        ]),
        ThemeCategory("Color", "attribute", verb="had it painted", pool=[
            "cherry red", "midnight blue", "cream white", "forest green",
            "chrome silver", "sunburst yellow", "coral pink", "matte black",
            "turquoise", "burnt orange",
        ]),
        ThemeCategory("Space", "ordinal", unit="space", pool=[]),
    ],
)

MASQUERADE_BALL = ScenarioTheme(
    name="Masquerade Ball",
    title_patterns=["The {noun} Masquerade", "The {noun} Ball"],
    title_nouns=["Midnight", "Winter", "Velvet", "Silver", "Grand", "Hidden"],
    intro_openers=["As the orchestra began", "Under the chandeliers", "As the masks came out"],
    intro_template="{opener}, seven guests swept into the ballroom. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Guest", "person", pool=[
            "the Baroness", "the Merchant", "the Poet", "the Diplomat", "the Twin",
            "the Stranger", "the Composer", "the Painter", "the Duchess", "the Officer",
            "the Bride", "the Magistrate",
        ]),
        ThemeCategory("Mask", "attribute", verb="wore", pool=[
            "a silver mask", "a feathered mask", "a black lace mask", "a golden mask",
            "a jeweled mask", "a porcelain mask", "a peacock mask", "a mirrored mask",
            "a velvet mask", "a beaded mask",
        ]),
        ThemeCategory("Dance", "attribute", verb="opened with", pool=[
            "a waltz", "a tango", "a quadrille", "a minuet", "a foxtrot",
            "a polka", "a mazurka", "a two-step", "a reel", "a gavotte",
        ]),
        ThemeCategory("Arrival", "ordinal", unit="arrival", pool=[]),
    ],
)

FARMERS_MARKET = ScenarioTheme(
    name="Farmers Market",
    title_patterns=["The {noun} Market", "The {noun} Farm Stand"],
    title_nouns=["Saturday", "Harvest", "Riverside", "Town Square", "Autumn", "Weekly"],
    intro_openers=["As the stalls opened", "Under the morning mist", "As the first customers arrived"],
    intro_template="{opener}, seven vendors set up their stalls. Use the clues to match "
                    "each {subject} to their {axes}.",
    categories=[
        ThemeCategory("Vendor", "person", pool=[
            "Marigold", "Otho", "Perry", "Sunniva", "Cleo", "Barnabas", "Wren",
            "Idris", "Coraline", "Fenn", "Rosalie", "Dashiell",
        ]),
        ThemeCategory("Product", "attribute", verb="sold", pool=[
            "heirloom tomatoes", "wildflower honey", "goat cheese", "fresh-cut flowers",
            "sourdough bread", "maple syrup", "seasonal jam", "roasted coffee",
            "handmade soap", "smoked trout",
        ]),
        ThemeCategory("Stall", "attribute", verb="decorated", pool=[
            "a red-striped stall", "a green-striped stall", "a wooden crate stall",
            "a string-lit stall", "a chalkboard-sign stall", "a canvas-awning stall",
            "a flower-draped stall", "a burlap-lined stall", "a rustic-barrel stall",
            "a painted-sign stall",
        ]),
        ThemeCategory("Booth", "ordinal", unit="booth", pool=[]),
    ],
)

THEMES = {
    "manor_mystery": MANOR_MYSTERY, "track_meet": TRACK_MEET,
    "wine_tasting": WINE_TASTING, "bake_off": BAKE_OFF, "chess_open": CHESS_OPEN,
    "gallery_opening": GALLERY_OPENING, "cruise_mystery": CRUISE_MYSTERY,
    "film_festival": FILM_FESTIVAL, "spelling_bee": SPELLING_BEE,
    "antique_auction": ANTIQUE_AUCTION, "jazz_club": JAZZ_CLUB, "garden_show": GARDEN_SHOW,
    "regatta": REGATTA, "cooking_competition": COOKING_COMPETITION, "poetry_slam": POETRY_SLAM,
    "science_fair": SCIENCE_FAIR, "vintage_car_show": VINTAGE_CAR_SHOW,
    "masquerade_ball": MASQUERADE_BALL, "farmers_market": FARMERS_MARKET,
}
