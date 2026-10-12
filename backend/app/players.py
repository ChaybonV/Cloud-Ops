import json
from pathlib import Path

# backend/data/players.json
PLAYERS_FILE = Path(__file__).resolve().parent.parent / "data" / "players.json"


def load_players():
    """Leest de dataset en geeft de lijst met spelers terug."""
    with open(PLAYERS_FILE, encoding="utf-8") as file:
        dataset = json.load(file)
    return dataset["players"]
