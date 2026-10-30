# -------------------------
# Tests voor de backend.
#
# Deel 1 test de logica (recommender.py) met zelfgemaakte testspelers.
# Deel 2 test de API (main.py) met de echte dataset.
#
# pytest voert elke functie uit waarvan de naam begint met "test_".
# "assert" betekent: controleer dat dit klopt. Klopt het niet, dan faalt de test.
# Bv. "assert result["count"] == 10" -> het aantal moet 10 zijn.
#
# Uitvoeren in de map backend:  python -m pytest
# -------------------------

from fastapi.testclient import TestClient

from app.main import app
from app.recommender import ATTRIBUTE_LABELS, POSITION_LABELS, ROLE_PROFILES, recommend, role_score


# =============================================================================
# Deel 1: de logica (recommender.py)
# =============================================================================


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


# =============================================================================
# Deel 2: de API (main.py)
# =============================================================================

# De TestClient roept de API aan zonder dat de server moet draaien.
# Deze tests gebruiken de echte dataset uit data/players.json.
client = TestClient(app)


def test_geeft_de_baseline_aanbevelingen_terug():
    response = client.get("/api/recommendations")
    result = response.json()

    assert response.status_code == 200
    assert result["strategy"] == "role_score_baseline"
    assert result["personalized"] is False
    assert result["count"] == 10
    assert len(result["recommendations"]) == 10


def test_aanbevelingen_staan_van_hoge_naar_lage_score():
    result = client.get("/api/recommendations?limit=50").json()

    previous_score = 100
    for player in result["recommendations"]:
        assert player["score"] <= previous_score
        previous_score = player["score"]


def test_past_filters_uit_de_query_toe():
    url = "/api/recommendations?position=AM&max_age=23&max_market_value=5000000&min_minutes=900"
    result = client.get(url).json()

    assert result["count"] > 0
    for player in result["recommendations"]:
        assert player["position"] == "AM"
        assert player["age"] <= 23
        assert player["market_value_eur"] <= 5_000_000
        assert player["minutes"] >= 900


def test_limit_bepaalt_het_aantal_aanbevelingen():
    result = client.get("/api/recommendations?limit=3").json()

    assert result["count"] == 3
    assert result["total_matching"] > 3


def test_weigert_ongeldige_parameters():
    invalid_queries = [
        "limit=0",
        "limit=51",
        "position=XX",
        "league=Bestaat niet",
        "max_age=oud",
        "max_age=5",
        "max_market_value=-1",
        "min_minutes=-1",
    ]
    for query in invalid_queries:
        response = client.get("/api/recommendations?" + query)
        assert response.status_code == 422


def test_geeft_de_keuzes_voor_de_filters():
    options = client.get("/api/options").json()

    assert "Jupiler Pro League" in options["leagues"]
    assert options["positions"]["AM"] == "Aanvallende middenvelder"


def test_dashboard_mag_de_api_aanroepen():
    # Het dashboard draait op een ander adres; de API moet dat toelaten (CORS).
    response = client.get("/api/options", headers={"Origin": "http://localhost:8080"})

    assert response.headers["access-control-allow-origin"] == "*"


def test_onbekende_route_geeft_404():
    assert client.get("/bestaat-niet").status_code == 404
