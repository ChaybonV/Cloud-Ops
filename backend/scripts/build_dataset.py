"""Bouwt data/players.json uit twee open datasets, als ETL (zoals in Data Engineering).

Uitvoeren vanuit de map backend (pandas moet geïnstalleerd zijn):

    pip install pandas
    python scripts/build_dataset.py

- EA Sports FC 26: individuele eigenschappen per speler (0-100).
- Transfermarkt: marktwaarde, leeftijd, club en cijfers van seizoen 2025/26.

De bronbestanden staan in data/bronnen/ (zie de README voor waar ze vandaan
komen). Een speler komt in de dataset als hij in beide bronnen staat met
dezelfde naam en een passende leeftijd.

De functie main onderaan volgt de drie stappen van ETL:
1. Extract: de bronbestanden inlezen.
2. Transform: filteren, optellen en de twee bronnen koppelen.
3. Load: het resultaat wegschrijven naar data/players.json.
"""

import json
import unicodedata

import pandas as pd

# Paden vanaf de map backend (daar start je het script).
SOURCE_FOLDER = "data/bronnen/"
OUTPUT_FILE = "data/players.json"

SEASON = "2025/2026"
SEASON_START = "2025-07-01"
SEASON_END = "2026-06-30"
# Leeftijd en marktwaarde gelden op het einde van het seizoen: 30 juni 2026.
REFERENCE_YEAR = 2026
REFERENCE_MONTH = 6
REFERENCE_DAY = 30

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


# =============================================================================
# Hulpfuncties
# =============================================================================


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
    """Berekent de leeftijd op 30 juni 2026 uit een datum zoals '2001-05-17 00:00:00'."""
    year = int(date_of_birth[0:4])
    month = int(date_of_birth[5:7])
    day = int(date_of_birth[8:10])

    age = REFERENCE_YEAR - year
    # Wie op de peildatum nog niet verjaard is, is een jaar jonger.
    if month > REFERENCE_MONTH:
        age = age - 1
    elif month == REFERENCE_MONTH and day > REFERENCE_DAY:
        age = age - 1
    return age


# =============================================================================
# Transform
# =============================================================================


def season_totals(appearances):
    """Telt per speler de competitiewedstrijden van het seizoen op.

    Geeft een tabel terug met per speler: minutes_played, goals, assists, matches.
    """
    # Enkel wedstrijden uit onze competities en uit dit seizoen.
    season = appearances[appearances["competition_id"].isin(LEAGUES.keys())]
    season = season[(season["date"] >= SEASON_START) & (season["date"] <= SEASON_END)]

    # Per speler de minuten, doelpunten en assists optellen.
    totals = season.groupby("player_id")[["minutes_played", "goals", "assists"]].sum()
    # Het aantal rijen per speler = het aantal wedstrijden.
    totals["matches"] = season.groupby("player_id").size()

    # player_id terug een gewone kolom maken, zodat we er later op kunnen koppelen.
    return totals.reset_index()


def usable_transfermarkt_players(tm_players, totals):
    """Houdt de Transfermarkt-spelers over die we kunnen gebruiken."""
    players = tm_players
    # Speelde dit seizoen in onze competities.
    players = players[players["player_id"].isin(totals["player_id"])]
    # Speelt nu bij een club uit onze competities.
    players = players[players["current_club_domestic_competition_id"].isin(LEAGUES.keys())]
    # Marktwaarde en geboortedatum zijn ingevuld.
    players = players.dropna(subset=["market_value_in_eur", "date_of_birth"])

    # .copy(): een eigen kopie, zodat we er kolommen aan mogen toevoegen.
    players = players.copy()
    players["age"] = players["date_of_birth"].apply(age_on_reference_date)
    players["match_name"] = players["name"].apply(normalise)
    return players


def usable_ea_players(ea_players):
    """Houdt de EA-spelers met een bekende positie over, met enkel de kolommen die we nodig hebben."""
    columns = ["Name", "Age", "Position"]
    for column in ATTRIBUTES:
        columns.append(column)
    for column in GOALKEEPER_ATTRIBUTES:
        if column not in columns:
            columns.append(column)

    players = ea_players[ea_players["Position"].isin(POSITION_GROUPS.keys())]
    players = players[columns].copy()
    players["match_name"] = players["Name"].apply(normalise)
    return players


def link_players(tm_players, ea_players):
    """Koppelt elke Transfermarkt-speler aan zijn EA-speler.

    Een koppeling telt alleen als er precies één EA-speler is met dezelfde
    naam en een passende leeftijd. Bij twee of meer weten we niet welke de
    juiste is, en laten we de speler weg.
    """
    # Alle combinaties met dezelfde (genormaliseerde) naam.
    linked = tm_players.merge(ea_players, on="match_name", how="inner")

    # De EA-leeftijd dateert van de start van het seizoen: de speler is daar
    # even oud of een jaar jonger dan op onze peildatum.
    difference = linked["age"] - linked["Age"]
    linked = linked[(difference == 0) | (difference == 1)]

    # Alleen spelers die precies één keer voorkomen.
    counts = linked["player_id"].value_counts()
    unique_ids = counts[counts == 1].index
    return linked[linked["player_id"].isin(unique_ids)]


# =============================================================================
# Load
# =============================================================================


def build_record(row):
    """Maakt het record van één speler zoals het in players.json komt."""
    position = POSITION_GROUPS[row["Position"]]

    # Een lege cel is in pandas "NaN"; in de dataset zetten we dan een lege tekst.
    nationality = row["country_of_citizenship"]
    if pd.isna(nationality):
        nationality = ""

    # int(...) maakt van de getallen uit pandas gewone Python-getallen,
    # anders kan json ze niet wegschrijven.
    record = {
        "id": "tm-" + str(row["player_id"]),
        "name": row["name"],
        "club": row["current_club_name"],
        "league": LEAGUES[row["current_club_domestic_competition_id"]],
        "nationality": nationality,
        "position": position,
        "age": int(row["age"]),
        "market_value_eur": int(row["market_value_in_eur"]),
        "matches": int(row["matches"]),
        "minutes": int(row["minutes_played"]),
        "goals": int(row["goals"]),
        "assists": int(row["assists"]),
    }

    # De eigenschappen uit EA toevoegen. Doelmannen hebben andere kolommen.
    if position == "GK":
        columns = GOALKEEPER_ATTRIBUTES
    else:
        columns = ATTRIBUTES
    for column in columns:
        attribute = columns[column]
        record[attribute] = int(row[column])

    return record


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


# =============================================================================
# Het script
# =============================================================================


def main():
    # 1. Extract: de bronbestanden inlezen. pandas pakt de .gz-bestanden zelf uit.
    appearances = pd.read_csv(SOURCE_FOLDER + "transfermarkt_appearances.csv.gz")
    tm_players = pd.read_csv(SOURCE_FOLDER + "transfermarkt_players.csv.gz")
    # "utf-8-sig": het EA-bestand begint met een onzichtbaar teken dat we overslaan.
    ea_players = pd.read_csv(SOURCE_FOLDER + "ea_fc_26_players.csv", encoding="utf-8-sig")

    # 2. Transform: filteren, optellen en koppelen.
    totals = season_totals(appearances)
    tm_players = usable_transfermarkt_players(tm_players, totals)
    ea_players = usable_ea_players(ea_players)
    linked = link_players(tm_players, ea_players)
    linked = linked.merge(totals, on="player_id", how="inner")

    # 3. Load: per speler een record maken en alles wegschrijven.
    records = []
    for index, row in linked.iterrows():
        records.append(build_record(row))
    write_dataset(records)

    print(str(len(records)) + " van " + str(len(tm_players)) + " spelers gekoppeld en weggeschreven")


if __name__ == "__main__":
    main()
