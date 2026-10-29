from app.positions import ATTRIBUTE_LABELS, POSITION_LABELS, ROLE_PROFILES
from app.recommender import recommend, role_score


def make_player(player_id, position, level):
    """Maakt een testspeler waarvan elke eigenschap gelijk is aan `level`."""
    player = {
        "id": player_id,
        "position": position,
        "league": "Testliga",
        "age": 24,
        "market_value_eur": 2_000_000,
        "minutes": 1800,
    }
    for attribute in ATTRIBUTE_LABELS:
        player[attribute] = level
    return player


# Vier testspelers met een bekende score, zodat we de uitkomst kunnen voorspellen.
st_weak = make_player("st-weak", "ST", 60)
st_weak["age"] = 21
st_weak["market_value_eur"] = 1_000_000

st_top = make_player("st-top", "ST", 90)
st_top["age"] = 30
st_top["market_value_eur"] = 40_000_000

st_sub = make_player("st-sub", "ST", 70)
st_sub["minutes"] = 200

cb_top = make_player("cb-top", "CB", 80)
cb_top["league"] = "Andere liga"

PLAYERS = [st_weak, st_top, st_sub, cb_top]


def get_ids(results):
    ids = []
    for player in results:
        ids.append(player["id"])
    return ids


def test_rolscore_is_het_gewogen_gemiddelde_van_het_rolprofiel():
    striker = make_player("st", "ST", 50)
    striker["finishing"] = 100

    # Afwerken weegt 0.3 bij een spits: 0.3 * 100 + 0.7 * 50 = 65.
    assert role_score(striker) == 65.0


def test_elke_positie_heeft_een_rolprofiel_met_totaalgewicht_1():
    for position in POSITION_LABELS:
        profile = ROLE_PROFILES[position]
        total_weight = sum(profile.values())
        assert round(total_weight, 5) == 1
        for attribute in profile:
            assert attribute in ATTRIBUTE_LABELS


def test_rangschikt_op_rolscore():
    result = recommend(PLAYERS)
    results = result["recommendations"]
    total = result["total_matching"]

    assert get_ids(results) == ["st-top", "cb-top", "st-sub", "st-weak"]
    assert total == 4
    assert results[0]["score"] == 90.0
    assert results[0]["position_label"] == "Spits"
    assert len(results[0]["score_breakdown"]) == len(ROLE_PROFILES["ST"])


def test_filtert_op_positie():
    results = recommend(PLAYERS, position="CB")["recommendations"]
    assert get_ids(results) == ["cb-top"]


def test_filtert_op_competitie():
    results = recommend(PLAYERS, league="Andere liga")["recommendations"]
    assert get_ids(results) == ["cb-top"]


def test_filtert_op_leeftijd():
    results = recommend(PLAYERS, max_age=21)["recommendations"]
    assert get_ids(results) == ["st-weak"]


def test_filtert_op_marktwaarde():
    results = recommend(PLAYERS, max_market_value=1_500_000)["recommendations"]
    assert get_ids(results) == ["st-weak"]


def test_filtert_op_minuten():
    results = recommend(PLAYERS, min_minutes=900)["recommendations"]
    assert "st-sub" not in get_ids(results)


def test_limit_beperkt_de_lijst_maar_niet_het_totaal():
    result = recommend(PLAYERS, limit=2)
    results = result["recommendations"]
    total = result["total_matching"]

    assert get_ids(results) == ["st-top", "cb-top"]
    assert total == 4
