from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from app.players import load_players
from app.positions import POSITION_LABELS
from app.recommender import DEFAULT_LIMIT, MAX_LIMIT, recommend

# De map frontend/ staat naast backend/ in de repository.
FRONTEND_DIRECTORY = Path(__file__).resolve().parents[2] / "frontend"


def create_app(players=None):
    players = load_players() if players is None else players
    leagues = sorted({player["league"] for player in players})

    app = FastAPI(
        title="Football Scout Recommender",
        description="Baseline-aanbevelingen voor spelersrekrutering.",
    )

    @app.get("/api/recommendations")
    def recommendations(
        position: Annotated[str | None, Query(description="Bv. AM of CB.")] = None,
        league: Annotated[str | None, Query(description="Naam van de competitie.")] = None,
        max_age: Annotated[int | None, Query(ge=15)] = None,
        max_market_value: Annotated[
            int | None, Query(ge=0, description="Maximale marktwaarde in euro.")
        ] = None,
        min_minutes: Annotated[
            int, Query(ge=0, description="Minimum aantal gespeelde minuten dit seizoen.")
        ] = 0,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    ):
        if position is not None and position not in POSITION_LABELS:
            raise HTTPException(
                422, f"Onbekende positie. Kies uit: {', '.join(POSITION_LABELS)}."
            )
        if league is not None and league not in leagues:
            raise HTTPException(422, f"Onbekende competitie. Kies uit: {', '.join(leagues)}.")

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
        """De keuzes voor de filters: posities en competities."""
        return {"positions": POSITION_LABELS, "leagues": leagues}

    # Alles wat geen API-route is, komt uit de map met het dashboard.
    app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
    return app


app = create_app()
