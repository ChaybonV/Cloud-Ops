from app.positions import ATTRIBUTE_LABELS, POSITION_LABELS, ROLE_PROFILES

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def role_score(player):
    """Gewogen gemiddelde (0-100) van de eigenschappen die tellen voor de positie."""
    profile = ROLE_PROFILES[player["position"]]
    return round(sum(player[attribute] * weight for attribute, weight in profile.items()), 1)


def score_breakdown(player):
    """Toont per eigenschap de waarde en het gewicht waaruit de score bestaat."""
    profile = ROLE_PROFILES[player["position"]]
    return [
        {
            "attribute": attribute,
            "label": ATTRIBUTE_LABELS[attribute],
            "value": player[attribute],
            "weight": weight,
        }
        for attribute, weight in profile.items()
    ]


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
    Geeft (aanbevelingen, aantal spelers dat aan de filters voldoet) terug.
    """
    candidates = [
        player
        for player in players
        if (position is None or player["position"] == position)
        and (league is None or player["league"] == league)
        and (max_age is None or player["age"] <= max_age)
        and (max_market_value is None or player["market_value_eur"] <= max_market_value)
        and player["minutes"] >= min_minutes
    ]
    # Bij een gelijke score staat de goedkoopste speler eerst.
    candidates.sort(key=lambda player: (-role_score(player), player["market_value_eur"]))
    recommendations = [
        {
            **player,
            "position_label": POSITION_LABELS[player["position"]],
            "score": role_score(player),
            "score_breakdown": score_breakdown(player),
        }
        for player in candidates[:limit]
    ]
    return recommendations, len(candidates)
