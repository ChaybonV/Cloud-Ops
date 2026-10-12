import pytest
from fastapi.testclient import TestClient

from app.main import app, create_app
from tests.test_recommender import PLAYERS

client = TestClient(create_app(PLAYERS))


def test_geeft_de_baseline_aanbevelingen_terug():
    response = client.get("/api/recommendations", params={"limit": 2})
    result = response.json()

    assert response.status_code == 200
    assert result["strategy"] == "role_score_baseline"
    assert result["personalized"] is False
    assert result["total_matching"] == 4
    assert result["count"] == 2
    assert [player["id"] for player in result["recommendations"]] == ["st-top", "cb-top"]


def test_past_filters_uit_de_query_toe():
    response = client.get(
        "/api/recommendations",
        params={"position": "ST", "max_age": 25, "max_market_value": 1_500_000},
    )

    assert [player["id"] for player in response.json()["recommendations"]] == ["st-weak"]


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 51}, {"position": "XX"}, {"league": "Bestaat niet"}, {"max_age": "oud"}],
)
def test_weigert_ongeldige_parameters(params):
    assert client.get("/api/recommendations", params=params).status_code == 422


def test_geeft_de_keuzes_voor_de_filters():
    options = client.get("/api/options").json()

    assert options["leagues"] == ["Andere liga", "Testliga"]
    assert options["positions"]["AM"] == "Aanvallende middenvelder"


def test_serveert_het_dashboard():
    assert "Football Scout" in client.get("/").text
    assert client.get("/bestaat-niet").status_code == 404


def test_werkt_met_de_echte_dataset():
    result = TestClient(app).get("/api/recommendations", params={"position": "GK"}).json()

    assert result["count"] == 10
    assert all(player["position"] == "GK" for player in result["recommendations"])
