from app.positions import ATTRIBUTE_LABELS, POSITION_LABELS, ROLE_PROFILES

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
