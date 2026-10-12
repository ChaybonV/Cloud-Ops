"""Posities en de vaste rolprofielen van de baseline.

Een rolprofiel zegt welke eigenschappen tellen voor een positie en hoe zwaar
(de gewichten tellen op tot 1). De profielen zijn voor elke club gelijk: dit
is de niet-gepersonaliseerde baseline.
"""

POSITION_LABELS = {
    "GK": "Doelman",
    "CB": "Centrale verdediger",
    "FB": "Vleugelverdediger",
    "DM": "Verdedigende middenvelder",
    "CM": "Centrale middenvelder",
    "AM": "Aanvallende middenvelder",
    "W": "Vleugelspeler",
    "ST": "Spits",
}

ATTRIBUTE_LABELS = {
    "pace": "Snelheid",
    "dribbling": "Dribbelen",
    "finishing": "Afwerken",
    "positioning": "Positiespel in de aanval",
    "vision": "Spelinzicht",
    "crossing": "Voorzetten",
    "short_passing": "Korte passing",
    "long_passing": "Lange passing",
    "ball_control": "Balcontrole",
    "reactions": "Reactievermogen",
    "composure": "Kalmte aan de bal",
    "interceptions": "Intercepties",
    "heading_accuracy": "Koppen",
    "def_awareness": "Verdedigend inzicht",
    "standing_tackle": "Tackles",
    "stamina": "Uithouding",
    "strength": "Kracht",
    "gk_diving": "Duiken",
    "gk_handling": "Balvastheid",
    "gk_kicking": "Uittrappen",
    "gk_positioning": "Positiespel in doel",
}

ROLE_PROFILES = {
    "GK": {
        "gk_diving": 0.25,
        "gk_positioning": 0.25,
        "gk_handling": 0.2,
        "reactions": 0.2,
        "gk_kicking": 0.1,
    },
    "CB": {
        "def_awareness": 0.25,
        "standing_tackle": 0.2,
        "interceptions": 0.15,
        "heading_accuracy": 0.15,
        "strength": 0.15,
        "short_passing": 0.1,
    },
    "FB": {
        "pace": 0.2,
        "standing_tackle": 0.2,
        "interceptions": 0.15,
        "crossing": 0.15,
        "stamina": 0.15,
        "short_passing": 0.15,
    },
    "DM": {
        "interceptions": 0.2,
        "standing_tackle": 0.2,
        "short_passing": 0.2,
        "def_awareness": 0.15,
        "strength": 0.15,
        "stamina": 0.1,
    },
    "CM": {
        "short_passing": 0.25,
        "vision": 0.2,
        "ball_control": 0.15,
        "stamina": 0.15,
        "interceptions": 0.15,
        "long_passing": 0.1,
    },
    "AM": {
        "vision": 0.25,
        "short_passing": 0.2,
        "dribbling": 0.2,
        "ball_control": 0.15,
        "finishing": 0.1,
        "composure": 0.1,
    },
    "W": {
        "pace": 0.25,
        "dribbling": 0.25,
        "crossing": 0.15,
        "finishing": 0.15,
        "vision": 0.1,
        "ball_control": 0.1,
    },
    "ST": {
        "finishing": 0.3,
        "positioning": 0.2,
        "pace": 0.15,
        "composure": 0.15,
        "heading_accuracy": 0.1,
        "ball_control": 0.1,
    },
}
