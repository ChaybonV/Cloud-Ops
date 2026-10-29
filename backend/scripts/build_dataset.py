"""Bouwt data/players.json uit twee open datasets.

    python scripts/build_dataset.py

- EA Sports FC 26: individuele eigenschappen per speler (0-100).
- Transfermarkt: marktwaarde, leeftijd, club en cijfers van seizoen 2025/26.

Een speler komt in de dataset als hij in beide bronnen staat met dezelfde
naam en een passende leeftijd.

Het script werkt in vier stappen (zie de functie main onderaan):
1. De seizoenscijfers per speler optellen (Transfermarkt).
2. De EA-spelers inlezen.
3. Elke Transfermarkt-speler koppelen aan zijn EA-speler.
4. Het resultaat wegschrijven naar data/players.json.
"""

import csv
import gzip
import io
import json
import socket
import unicodedata
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

# De map backend/
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


# --- Downloaden -------------------------------------------------------------

# Op sommige netwerken werkt IPv6 niet en wacht Python daar minutenlang op.
# Daarom zetten we de IPv4-adressen vooraan, zodat die eerst geprobeerd worden.
original_getaddrinfo = socket.getaddrinfo


def getaddrinfo_ipv4_first(host, port, family=0, type=0, proto=0, flags=0):
    # Dezelfde parameters als de originele functie, die we gewoon doorgeven.
    addresses = original_getaddrinfo(host, port, family, type, proto, flags)
    ipv4_addresses = []
    other_addresses = []
    for address in addresses:
        if address[0] == socket.AF_INET:
            ipv4_addresses.append(address)
        else:
            other_addresses.append(address)
    return ipv4_addresses + other_addresses


socket.getaddrinfo = getaddrinfo_ipv4_first


def download(url, filename):
    """Downloadt een bestand naar data/cache en geeft het pad terug.

    Staat het bestand er al, dan wordt het niet opnieuw gedownload.
    """
    cache_file = CACHE_DIRECTORY / filename
    if not cache_file.exists():
        print(filename + " downloaden...")
        CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        response = urllib.request.urlopen(url, timeout=60)
        cache_file.write_bytes(response.read())
        response.close()
    return cache_file


def open_transfermarkt(table):
    """Opent een Transfermarkt-tabel (een gezipt CSV-bestand) om te lezen."""
    url = TRANSFERMARKT_URL + "/" + table + ".csv.gz"
    path = download(url, "transfermarkt_" + table + ".csv.gz")
    return gzip.open(path, "rt", encoding="utf-8", newline="")


# --- Hulpfuncties -----------------------------------------------------------


def normalise(name):
    """Maakt van 'Kylian Mbappé' 'kylian mbappe', zodat schrijfwijzen overeenkomen."""
    # Accenten losmaken van de letters en daarna weggooien: é -> e.
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode()
    # Kleine letters, streepjes worden spaties, dubbele spaties verdwijnen.
    name = name.lower().replace("-", " ")
    words = name.split()
    return " ".join(words)


def age_on_reference_date(date_of_birth):
    """Berekent de leeftijd op de peildatum uit een datum zoals '2001-05-17 00:00:00'."""
    born = date.fromisoformat(date_of_birth[:10])
    age = REFERENCE_DATE.year - born.year
    # Wie dat jaar nog niet verjaard is, is een jaar jonger.
    if (born.month, born.day) > (REFERENCE_DATE.month, REFERENCE_DATE.day):
        age = age - 1
    return age


# --- Stap 1: seizoenscijfers per speler -------------------------------------


def load_season_totals():
    """Telt per speler de competitiewedstrijden van het seizoen op.

    Geeft een dictionary terug: speler-id -> {matches, minutes, goals, assists}.
    """
    totals = {}
    file = open_transfermarkt("appearances")
    for row in csv.DictReader(file):
        # Enkel wedstrijden uit onze competities en uit dit seizoen.
        if row["competition_id"] not in LEAGUES:
            continue
        if row["date"] < SEASON_START or row["date"] > SEASON_END:
            continue

        player_id = row["player_id"]
        if player_id not in totals:
            totals[player_id] = {"matches": 0, "minutes": 0, "goals": 0, "assists": 0}

        totals[player_id]["matches"] += 1
        totals[player_id]["minutes"] += int(row["minutes_played"])
        totals[player_id]["goals"] += int(row["goals"])
        totals[player_id]["assists"] += int(row["assists"])
    file.close()
    return totals


# --- Stap 2: EA-spelers inlezen ---------------------------------------------


def load_ea_players_by_name():
    """Leest de EA-spelers in.

    Geeft een dictionary terug: genormaliseerde naam -> lijst van EA-spelers
    met die naam (meestal één, soms meerdere).
    """
    path = download(EA_URL, "ea_fc_26.zip")
    archive = zipfile.ZipFile(path)
    file = io.TextIOWrapper(archive.open(EA_FILE), encoding="utf-8-sig")

    by_name = {}
    for row in csv.DictReader(file):
        if row["Position"] not in POSITION_GROUPS:
            continue
        name = normalise(row["Name"])
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(row)

    archive.close()
    return by_name


# --- Stap 3: koppelen -------------------------------------------------------


def find_ea_player(ea_players_by_name, name, age):
    """Zoekt de EA-speler met dezelfde naam en een passende leeftijd.

    Geeft None terug als er geen is, of als er meerdere zijn (dan weten we
    niet welke de juiste is).
    """
    same_name = ea_players_by_name.get(normalise(name), [])

    candidates = []
    for row in same_name:
        # De EA-leeftijd dateert van de start van het seizoen: de speler is
        # daar even oud of een jaar jonger dan op onze peildatum.
        difference = age - int(row["Age"])
        if difference == 0 or difference == 1:
            candidates.append(row)

    if len(candidates) == 1:
        return candidates[0]
    return None


def build_record(profile, totals, ea_player, age):
    """Maakt het record van één speler zoals het in players.json komt."""
    position = POSITION_GROUPS[ea_player["Position"]]

    record = {
        "id": "tm-" + profile["player_id"],
        "name": profile["name"],
        "club": profile["current_club_name"],
        "league": LEAGUES[profile["current_club_domestic_competition_id"]],
        "nationality": profile["country_of_citizenship"],
        "position": position,
        "age": age,
        "market_value_eur": int(float(profile["market_value_in_eur"])),
        "matches": totals["matches"],
        "minutes": totals["minutes"],
        "goals": totals["goals"],
        "assists": totals["assists"],
    }

    # De eigenschappen uit EA toevoegen. Doelmannen hebben andere kolommen.
    if position == "GK":
        columns = GOALKEEPER_ATTRIBUTES
    else:
        columns = ATTRIBUTES
    for column in columns:
        attribute = columns[column]
        record[attribute] = int(ea_player[column])

    return record


# --- Stap 4: wegschrijven ---------------------------------------------------


def write_dataset(records):
    """Schrijft de spelers naar data/players.json, één speler per regel."""
    meta = {
        "season": SEASON,
        "sources": ["EA Sports FC 26 (eigenschappen)", "Transfermarkt (waarde en seizoen)"],
        "player_count": len(records),
    }

    # "w" overschrijft het bestand: de oude inhoud verdwijnt.
    file = open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n")
    file.write("{\n")
    file.write('"meta": ' + json.dumps(meta, ensure_ascii=False) + ",\n")
    file.write('"players": [\n')
    number = 0
    for record in records:
        number = number + 1
        line = json.dumps(record, ensure_ascii=False)
        # Na elke speler komt een komma, behalve na de laatste.
        if number < len(records):
            line = line + ","
        file.write(line + "\n")
    file.write("]\n")
    file.write("}\n")
    file.close()


def main():
    totals = load_season_totals()
    ea_players_by_name = load_ea_players_by_name()

    records = []
    candidates = 0
    file = open_transfermarkt("players")
    for profile in csv.DictReader(file):
        # Sla spelers over die we niet kunnen gebruiken.
        if profile["player_id"] not in totals:
            continue  # speelde dit seizoen niet in onze competities
        if profile["current_club_domestic_competition_id"] not in LEAGUES:
            continue  # speelt nu bij een club buiten onze competities
        if profile["market_value_in_eur"] == "" or profile["date_of_birth"] == "":
            continue  # marktwaarde of geboortedatum ontbreekt
        candidates = candidates + 1

        age = age_on_reference_date(profile["date_of_birth"])
        ea_player = find_ea_player(ea_players_by_name, profile["name"], age)
        if ea_player is not None:
            player_totals = totals[profile["player_id"]]
            records.append(build_record(profile, player_totals, ea_player, age))
    file.close()

    write_dataset(records)
    print(str(len(records)) + " van " + str(candidates) + " spelers gekoppeld en weggeschreven")


if __name__ == "__main__":
    main()
