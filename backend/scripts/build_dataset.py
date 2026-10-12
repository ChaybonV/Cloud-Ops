"""Bouwt data/players.json uit twee open datasets.

    python scripts/build_dataset.py

- EA Sports FC 26: individuele eigenschappen per speler (0-100).
- Transfermarkt: marktwaarde, leeftijd, club en cijfers van seizoen 2025/26.

Een speler komt in de dataset als hij in beide bronnen staat met dezelfde
naam en een passende leeftijd.
"""

import csv
import gzip
import io
import json
import socket
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "players.json"
CACHE_DIRECTORY = ROOT / "data" / "cache"

EA_URL = "https://www.kaggle.com/api/v1/datasets/download/talhademirezen/fc-26-player-stats"
EA_FILE = "fc_26_players_stats.csv"
TRANSFERMARKT_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"

SEASON = "2025/2026"
SEASON_START = "2025-07-01"
SEASON_END = "2026-06-30"
# Leeftijd en marktwaarde gelden op het einde van het seizoen.
REFERENCE_DATE = date(2026, 6, 30)

# Competitiecode van Transfermarkt -> naam in de app.
LEAGUES = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
    "NL1": "Eredivisie",
    "PO1": "Liga Portugal",
    "BE1": "Jupiler Pro League",
    "TR1": "Süper Lig",
    "GR1": "Super League (Griekenland)",
    "SC1": "Scottish Premiership",
    "DK1": "Superligaen",
    "UKR1": "Premier Liga (Oekraïne)",
}

# Positie in EA FC -> positiegroep in de app.
POSITION_GROUPS = {
    "GK": "GK",
    "CB": "CB",
    "LB": "FB",
    "RB": "FB",
    "CDM": "DM",
    "CM": "CM",
    "CAM": "AM",
    "LM": "W",
    "RM": "W",
    "LW": "W",
    "RW": "W",
    "ST": "ST",
}

# Kolom in het EA-bestand -> naam van de eigenschap in de dataset.
ATTRIBUTES = {
    "Pace": "pace",
    "Dribbling": "dribbling",
    "Finishing": "finishing",
    "Positioning": "positioning",
    "Vision": "vision",
    "Crossing": "crossing",
    "Short Passing": "short_passing",
    "Long Passing": "long_passing",
    "Ball Control": "ball_control",
    "Reactions": "reactions",
    "Composure": "composure",
    "Interceptions": "interceptions",
    "Heading Accuracy": "heading_accuracy",
    "Def Awareness": "def_awareness",
    "Standing Tackle": "standing_tackle",
    "Stamina": "stamina",
    "Strength": "strength",
}
# Bij doelmannen bevatten deze kolommen de keeperseigenschappen.
GOALKEEPER_ATTRIBUTES = {
    "Pace": "gk_diving",
    "Shooting": "gk_handling",
    "Passing": "gk_kicking",
    "Physicality": "gk_positioning",
    "Reactions": "reactions",
}

# Op sommige netwerken werkt IPv6 niet en wacht Python daar minutenlang op.
# Daarom proberen we IPv4-adressen eerst.
_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda *args, **kwargs: sorted(
    _getaddrinfo(*args, **kwargs), key=lambda address: address[0] != socket.AF_INET
)


def download(url, filename):
    """Downloadt een bestand één keer naar data/cache en geeft het pad terug."""
    cache_file = CACHE_DIRECTORY / filename
    if not cache_file.exists():
        print(f"{filename} downloaden...")
        CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            cache_file.write_bytes(response.read())
    return cache_file


def read_transfermarkt(table):
    path = download(f"{TRANSFERMARKT_URL}/{table}.csv.gz", f"transfermarkt_{table}.csv.gz")
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def read_ea_players():
    path = download(EA_URL, "ea_fc_26.zip")
    with zipfile.ZipFile(path) as archive, archive.open(EA_FILE) as file:
        yield from csv.DictReader(io.TextIOWrapper(file, encoding="utf-8-sig"))


def normalise(name):
    """'Kylian Mbappé' -> 'kylian mbappe', zodat schrijfwijzen overeenkomen."""
    without_accents = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return " ".join(without_accents.lower().replace("-", " ").split())


def age_on_reference_date(date_of_birth):
    born = date.fromisoformat(date_of_birth[:10])
    had_birthday = (REFERENCE_DATE.month, REFERENCE_DATE.day) >= (born.month, born.day)
    return REFERENCE_DATE.year - born.year - (not had_birthday)


def load_season_totals():
    """Telt per speler de competitiewedstrijden van het seizoen op."""
    totals = defaultdict(lambda: {"matches": 0, "minutes": 0, "goals": 0, "assists": 0})
    for row in read_transfermarkt("appearances"):
        if row["competition_id"] in LEAGUES and SEASON_START <= row["date"] <= SEASON_END:
            player = totals[row["player_id"]]
            player["matches"] += 1
            player["minutes"] += int(row["minutes_played"])
            player["goals"] += int(row["goals"])
            player["assists"] += int(row["assists"])
    return totals


def load_ea_players_by_name():
    by_name = defaultdict(list)
    for row in read_ea_players():
        if row["Position"] in POSITION_GROUPS:
            by_name[normalise(row["Name"])].append(row)
    return by_name


def find_ea_player(ea_players_by_name, name, age):
    """Zoekt de EA-speler met dezelfde naam; None als er geen of meerdere zijn."""
    # De EA-leeftijd dateert van de start van het seizoen: even oud of een jaar jonger.
    candidates = [
        row
        for row in ea_players_by_name.get(normalise(name), [])
        if age - int(row["Age"]) in (0, 1)
    ]
    return candidates[0] if len(candidates) == 1 else None


def build_record(profile, totals, ea_player, age):
    position = POSITION_GROUPS[ea_player["Position"]]
    columns = GOALKEEPER_ATTRIBUTES if position == "GK" else ATTRIBUTES
    return {
        "id": f"tm-{profile['player_id']}",
        "name": profile["name"],
        "club": profile["current_club_name"],
        "league": LEAGUES[profile["current_club_domestic_competition_id"]],
        "nationality": profile["country_of_citizenship"],
        "position": position,
        "age": age,
        "market_value_eur": int(float(profile["market_value_in_eur"])),
        **totals,
        **{attribute: int(ea_player[column]) for column, attribute in columns.items()},
    }


def main():
    totals = load_season_totals()
    ea_players_by_name = load_ea_players_by_name()

    records = []
    candidates = 0
    for profile in read_transfermarkt("players"):
        in_scope = (
            profile["player_id"] in totals
            and profile["current_club_domestic_competition_id"] in LEAGUES
            and profile["market_value_in_eur"]
            and profile["date_of_birth"]
        )
        if not in_scope:
            continue
        candidates += 1
        age = age_on_reference_date(profile["date_of_birth"])
        ea_player = find_ea_player(ea_players_by_name, profile["name"], age)
        if ea_player is not None:
            records.append(build_record(profile, totals[profile["player_id"]], ea_player, age))

    meta = {
        "season": SEASON,
        "sources": ["EA Sports FC 26 (eigenschappen)", "Transfermarkt (waarde en seizoen)"],
        "player_count": len(records),
    }
    # Eén speler per regel houdt het bestand leesbaar.
    lines = ",\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    OUTPUT_FILE.write_text(
        f'{{\n"meta": {json.dumps(meta, ensure_ascii=False)},\n"players": [\n{lines}\n]\n}}\n',
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(records)} van {candidates} spelers gekoppeld en weggeschreven")


if __name__ == "__main__":
    main()
