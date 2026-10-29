# Cloud & Ops

## Football Scout Recommender

Een recommendation engine voor scouting en spelersrekrutering in het voetbal.
De app rangschikt spelers per positie op een vaste rolscore (de baseline).
De aanbevelingen zijn nog niet gepersonaliseerd, personalisatie per club en de AI-agent volgen later.

## Starten

Je hebt alleen [Docker Desktop](https://www.docker.com/products/docker-desktop/)
en Git nodig. Start Docker Desktop en voer dan uit:

```sh
git clone https://github.com/ChaybonV/Cloud-Ops.git
cd Cloud-Ops
docker compose up --build
```

De eerste keer duurt dat ongeveer een halve minuut. Daarna:

- dashboard: <http://localhost:8080>
- API-documentatie: <http://localhost:8000/docs>

Stoppen doe je met `Ctrl+C`, of met `docker compose down` in een andere
terminal.

### Instellingen

Zonder extra stappen staat het dashboard op poort 8080. Is die al in gebruik,
kopieer dan `.env.example` naar `.env` en kies daar een andere poort.
`.env` staat in `.gitignore` en komt dus nooit op GitHub. Daarom is het ook de
plek voor geheime sleutels, die zijn er nu nog niet.

### Zonder Docker

Voor het ontwikkelen kan je de twee delen ook rechtstreeks starten, met
Python 3.11 of hoger, elk in een eigen terminal. Het zijn dezelfde commando's
als in de containers.

Backend, in de map `backend`:

```sh
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend, in de map `frontend`:

```sh
python -m http.server 8080
```

### Tests

De tests draaien automatisch bij elke push (zie [CI](#ci)). Lokaal voer je
ze uit in de map `backend`:

```sh
python -m pytest
```

## API

`GET /api/recommendations` geeft de shortlist terug. Alle filters zijn
optioneel:

| Parameter | Betekenis |
|---|---|
| `position` | `GK`, `CB`, `FB`, `DM`, `CM`, `AM`, `W` of `ST` |
| `league` | Naam van de competitie, bv. `Jupiler Pro League` |
| `max_age` | Maximale leeftijd |
| `max_market_value` | Maximale marktwaarde in euro |
| `min_minutes` | Minimum aantal gespeelde minuten dit seizoen |
| `limit` | Aantal aanbevelingen, 1 tot 50 (standaard 10) |

Voorbeeld: aanvallende middenvelders van hoogstens 23 jaar en 5 miljoen euro. (Momenteel nog beperkte filters zonder personalisatie met extra info over clubtactiek of visie en AI-agent)

```
GET /api/recommendations?position=AM&max_age=23&max_market_value=5000000
```

`GET /api/options` geeft de posities en competities waaruit je kan kiezen.

## Baseline

Elke speler heeft individuele eigenschappen met een waarde van 0 tot 100,
zoals tackles, spelinzicht of afwerken. Per positie legt een **rolprofiel**
vast welke eigenschappen tellen en hoe zwaar (zie
[backend/app/positions.py](backend/app/positions.py)). De **rolscore** is het gewogen
gemiddelde van die eigenschappen.

Voorbeeld voor een spits:

| Eigenschap | Gewicht |
|---|---|
| Afwerken | 0,30 |
| Positiespel in de aanval | 0,20 |
| Snelheid | 0,15 |
| Kalmte aan de bal | 0,15 |
| Koppen | 0,10 |
| Balcontrole | 0,10 |

De baseline filtert de spelers en rangschikt ze op rolscore. Het antwoord
bevat per speler een `score_breakdown` die toont hoe de score is opgebouwd.

De rolprofielen zijn voor elke club gelijk. Ze houden geen rekening met de
speelstijl of de noden van een club; dat is wat de gepersonaliseerde versie
later toevoegt.

## Structuur

De app bestaat uit twee containers, die `docker-compose.yml` samen start:

| Container | Wat | Poort |
|---|---|---|
| `backend` | De API in Python (FastAPI), met de dataset. Zie `backend/Dockerfile`. | 8000 |
| `frontend` | Het dashboard. De ingebouwde webserver van Python serveert de HTML, CSS en JavaScript. Zie `frontend/Dockerfile`. | 8080 |

De gebruiker opent alleen het dashboard. Het dashboard haalt de aanbevelingen
op bij de API (het adres staat in `API_URL` bovenaan `frontend/app.js`).
Omdat de twee op een ander adres draaien, laat de API dat uitdrukkelijk toe
met CORS (zie `backend/app/main.py`).

```
.github/workflows/
  ci.yml               tests en Docker-build bij elke push
backend/
  app/
    main.py            API-endpoints (FastAPI)
    recommender.py     logica: rolscore, filteren en rangschikken
    positions.py       posities en rolprofielen
    players.py         inladen van de data
  data/players.json    dataset: één speler per regel
  scripts/
    build_dataset.py   bouwt data/players.json opnieuw op
  tests/
  Dockerfile           bouwt de backend-container
  .dockerignore        wat niet in de backend-container moet
  requirements.txt     Python-pakketten die de backend nodig heeft
frontend/
  index.html, app.js, styles.css
  Dockerfile           bouwt de frontend-container
docs/LOGBOEK-PORTFOLIO.md
docker-compose.yml     start beide containers
.env.example           voorbeeld van het bestand .env
```

## CI

Bij elke push, op elke branch, voert GitHub Actions
([.github/workflows/ci.yml](.github/workflows/ci.yml)) twee dingen uit:

1. de tests van de backend
2. het bouwen van beide Docker-containers

Het resultaat staat op GitHub onder het tabblad **Actions**.

## Data

`backend/data/players.json` bevat 4.244 spelers uit 13 Europese competities, seizoen
2025/2026: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie,
Liga Portugal, Jupiler Pro League, Süper Lig en de hoogste afdelingen van
Schotland, Denemarken, Griekenland en Oekraïne.

| Gegevens | Bron |
|---|---|
| Eigenschappen per speler (0-100) | EA Sports FC 26, via [Kaggle](https://www.kaggle.com/datasets/talhademirezen/fc-26-player-stats) |
| Marktwaarde, leeftijd, club, minuten, doelpunten, assists | Transfermarkt, via [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) |

De eigenschappen zijn inschattingen van EA Sports, geen gemeten
wedstrijdstatistieken. Ze zijn gekozen omdat ze elke speler individueel
beoordelen op elke positie, gratis en actuele wedstrijdstatistieken met
verdedigende cijfers zijn niet beschikbaar voor het publiek.

De twee bronnen worden gekoppeld op naam en leeftijd. Dat lukt voor 4.244 van
de 5.855 spelers. Wie in de twee bronnen anders gespeld is (bv. Vinicius
Junior) ontbreekt.

De dataset opnieuw opbouwen (in de map `backend`, downloadt ongeveer 50 MB):

```sh
python scripts/build_dataset.py
```
