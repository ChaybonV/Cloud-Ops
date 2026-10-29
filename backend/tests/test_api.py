# -------------------------
# Tests voor de API (main.py), met de echte dataset.
#
# pytest voert elke functie uit waarvan de naam begint met "test_".
# "assert" betekent: controleer dat dit klopt. Klopt het niet, dan faalt de test.
# Bv. "assert result["count"] == 10" -> het aantal moet 10 zijn.
#
# Uitvoeren in de map backend:  python -m pytest
# -------------------------

from fastapi.testclient import TestClient

from app.main import app

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
