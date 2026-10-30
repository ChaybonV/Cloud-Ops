"""De logica van de baseline: posities, rolprofielen en de rolscore.

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


DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def role_score(player):
    """Berekent de rolscore (0-100) van een speler.

    Elke eigenschap uit het rolprofiel van zijn positie wordt vermenigvuldigd
    met haar gewicht. De som daarvan is de score.
    """
    profile = ROLE_PROFILES[player["position"]]

    # Voor elke eigenschap: waarde x gewicht.
    parts = []
    for attribute in profile:
        weight = profile[attribute]
        parts.append(player[attribute] * weight)

    # sum() telt kommagetallen nauwkeuriger op dan zelf optellen in de lus.
    score = sum(parts)
    return round(score, 1)


def score_breakdown(player):
    """Geeft per eigenschap de waarde en het gewicht, zodat je ziet hoe de score is opgebouwd."""
    profile = ROLE_PROFILES[player["position"]]

    breakdown = []
    for attribute in profile:
        item = {
            "attribute": attribute,
            "label": ATTRIBUTE_LABELS[attribute],
            "value": player[attribute],
            "weight": profile[attribute],
        }
        breakdown.append(item)

    return breakdown


def passes_filters(player, position, league, max_age, max_market_value, min_minutes):
    """Geeft True als de speler aan alle ingevulde filters voldoet.

    Een filter dat None is, werd niet ingevuld en telt dus niet mee.
    """
    if position is not None and player["position"] != position:
        return False
    if league is not None and player["league"] != league:
        return False
    if max_age is not None and player["age"] > max_age:
        return False
    if max_market_value is not None and player["market_value_eur"] > max_market_value:
        return False
    if player["minutes"] < min_minutes:
        return False
    return True


def get_market_value(player):
    return player["market_value_eur"]


def recommend(
    players,
    position=None,
    league=None,
    max_age=None,
    max_market_value=None,
    min_minutes=0,
    limit=DEFAULT_LIMIT,
):
    """Baseline: filter de spelers en rangschik ze op rolscore.

    De score is voor elke gebruiker dezelfde; er is nog geen personalisatie.
    Geeft een dictionary terug met de aanbevelingen en het aantal spelers dat
    aan de filters voldoet.
    """
    # Stap 1: hou enkel de spelers over die aan de filters voldoen.
    candidates = []
    for player in players:
        if passes_filters(player, position, league, max_age, max_market_value, min_minutes):
            candidates.append(player)

    # Stap 2: sorteer op rolscore, van hoog naar laag.
    # We sorteren eerst op marktwaarde. Daardoor staat bij een gelijke score
    # de goedkoopste speler eerst.
    candidates.sort(key=get_market_value)
    candidates.sort(key=role_score, reverse=True)

    # Stap 3: neem de beste spelers en voeg de score toe aan hun gegevens.
    recommendations = []
    for player in candidates[:limit]:
        result = dict(player)  # een kopie, zodat de originele data niet verandert
        result["position_label"] = POSITION_LABELS[player["position"]]
        result["score"] = role_score(player)
        result["score_breakdown"] = score_breakdown(player)
        recommendations.append(result)

    return {
        "total_matching": len(candidates),
        "recommendations": recommendations,
    }
