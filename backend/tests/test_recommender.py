import pytest

from app.positions import ATTRIBUTE_LABELS, POSITION_LABELS, ROLE_PROFILES
from app.recommender import recommend, role_score


def make_player(player_id, position, level, **overrides):
    """Speler waarvan elke eigenschap gelijk is aan `level`."""
    player = {
        "id": player_id,
        "position": position,
        "league": "Testliga",
        "age": 24,
        "market_value_eur": 2_000_000,
        "minutes": 1800,
        **{attribute: level for attribute in ATTRIBUTE_LABELS},
    }
    player.update(overrides)
    return player


PLAYERS = [
    make_player("st-weak", "ST", 60, age=21, market_value_eur=1_000_000),
    make_player("st-top", "ST", 90, age=30, market_value_eur=40_000_000),
    make_player("st-sub", "ST", 70, minutes=200),
    make_player("cb-top", "CB", 80, league="Andere liga"),
]


def ids(results):
    return [player["id"] for player in results]


def test_rolscore_is_het_gewogen_gemiddelde_van_het_rolprofiel():
    striker = make_player("st", "ST", 50, finishing=100)

    # Afwerken weegt 0.3 bij een spits: 0.3 * 100 + 0.7 * 50.
    assert role_score(striker) == 65.0


def test_elke_positie_heeft_een_rolprofiel_met_totaalgewicht_1():
    assert set(ROLE_PROFILES) == set(POSITION_LABELS)
    for profile in ROLE_PROFILES.values():
        assert sum(profile.values()) == pytest.approx(1)
        assert set(profile) <= set(ATTRIBUTE_LABELS)


def test_rangschikt_op_rolscore():
    results, total = recommend(PLAYERS)

    assert ids(results) == ["st-top", "cb-top", "st-sub", "st-weak"]
    assert total == 4
    assert results[0]["score"] == 90.0
    assert results[0]["position_label"] == "Spits"
    assert len(results[0]["score_breakdown"]) == len(ROLE_PROFILES["ST"])


def test_filtert_op_positie_competitie_leeftijd_waarde_en_minuten():
    assert ids(recommend(PLAYERS, position="CB")[0]) == ["cb-top"]
    assert ids(recommend(PLAYERS, league="Andere liga")[0]) == ["cb-top"]
    assert ids(recommend(PLAYERS, max_age=21)[0]) == ["st-weak"]
    assert ids(recommend(PLAYERS, max_market_value=1_500_000)[0]) == ["st-weak"]
    assert "st-sub" not in ids(recommend(PLAYERS, min_minutes=900)[0])


def test_limit_beperkt_de_lijst_maar_niet_het_totaal():
    results, total = recommend(PLAYERS, limit=2)

    assert ids(results) == ["st-top", "cb-top"]
    assert total == 4
