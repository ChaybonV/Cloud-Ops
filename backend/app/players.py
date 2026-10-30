import json

# Het pad naar de dataset, vanaf de map backend.
# De server start altijd vanuit die map (lokaal én in de Docker-container).
PLAYERS_FILE = "data/players.json"


def load_players():
    """Leest de dataset en geeft de lijst met spelers terug."""
    file = open(PLAYERS_FILE, encoding="utf-8")
    dataset = json.load(file)
    file.close()
    return dataset["players"]
