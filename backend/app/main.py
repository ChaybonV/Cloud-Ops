from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.players import load_players
from app.positions import POSITION_LABELS
from app.recommender import DEFAULT_LIMIT, MAX_LIMIT, recommend

# De map frontend/ staat naast backend/ in de repository.
FRONTEND_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(
    title="Football Scout Recommender",
    description="Baseline-aanbevelingen voor spelersrekrutering.",
)

# De data wordt één keer ingeladen bij het opstarten.
players = load_players()

# Lijst van alle competities die in de data voorkomen, alfabetisch.
leagues = []
for player in players:
    if player["league"] not in leagues:
        leagues.append(player["league"])
leagues.sort()


# "str | None = None" betekent: de parameter is tekst, maar mag ook ontbreken.
@app.get("/api/recommendations")
def recommendations(
    position: str | None = None,
    league: str | None = None,
    max_age: int | None = None,
    max_market_value: int | None = None,
    min_minutes: int = 0,
    limit: int = DEFAULT_LIMIT,
):
    """Geeft de shortlist terug, gerangschikt op rolscore."""
    # Eerst controleren of de parameters geldig zijn. 422 = ongeldige invoer.
    if position is not None and position not in POSITION_LABELS:
        raise HTTPException(422, "Onbekende positie. Kies uit: " + ", ".join(POSITION_LABELS) + ".")
    if league is not None and league not in leagues:
        raise HTTPException(422, "Onbekende competitie. Kies uit: " + ", ".join(leagues) + ".")
    if max_age is not None and max_age < 15:
        raise HTTPException(422, "max_age moet minstens 15 zijn.")
    if max_market_value is not None and max_market_value < 0:
        raise HTTPException(422, "max_market_value mag niet negatief zijn.")
    if min_minutes < 0:
        raise HTTPException(422, "min_minutes mag niet negatief zijn.")
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(422, "limit moet tussen 1 en " + str(MAX_LIMIT) + " liggen.")

    results, total = recommend(
        players, position, league, max_age, max_market_value, min_minutes, limit
    )

    return {
        "strategy": "role_score_baseline",
        "personalized": False,
        "total_matching": total,
        "count": len(results),
        "recommendations": results,
    }


@app.get("/api/options")
def options():
    """Geeft de keuzes voor de filters: posities en competities."""
    return {"positions": POSITION_LABELS, "leagues": leagues}


# Alles wat geen API-route is, komt uit de map met het dashboard.
# Deze regel moet onderaan staan, anders vangt hij ook de API-routes op.
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
