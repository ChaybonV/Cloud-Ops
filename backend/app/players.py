import json
from pathlib import Path

PLAYERS_FILE = Path(__file__).resolve().parent.parent / "data" / "players.json"


def load_players(path=PLAYERS_FILE):
    """Leest de dataset en geeft de lijst met spelers terug."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)["players"]
