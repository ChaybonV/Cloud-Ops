# Cloud & Ops

## Football Scout Recommender

Een recommendation engine voor scouting en spelersrekrutering in het voetbal.
De app rangschikt spelers per positie op een vaste rolscore (de baseline).
De aanbevelingen zijn nog niet gepersonaliseerd, personalisatie per club en de AI-agent volgen later.

## Online

De app draait op Microsoft Azure:

- **dashboard:** <https://scout-frontend.yellowdune-90943d99.belgiumcentral.azurecontainerapps.io>
- **API-documentatie:** <https://scout-backend.yellowdune-90943d99.belgiumcentral.azurecontainerapps.io/docs>

Als niemand de app gebruikt, staan de containers uit (zie [Kosten](#kosten)).
Het eerste bezoek kan daardoor enkele seconden duren.

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

De instellingen staan in een bestand `.env` in de hoofdmap. Dat bestand staat
in `.gitignore` en komt dus nooit op GitHub. Daarom is het ook de plek voor
geheime sleutels.

Zonder `.env` werkt de app ook: `docker-compose.yml` gebruikt dan de
standaardwaarden. Wil je iets aanpassen, maak dan zelf een `.env` aan:

| Instelling | Betekenis | Standaard |
|---|---|---|
| `FRONTEND_PORT` | De poort op je pc waarop het dashboard bereikbaar is | `8080` |

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
[backend/app/recommender.py](backend/app/recommender.py)). De **rolscore** is het gewogen
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
op bij de API (het adres staat in `API_URL`, bovenaan de JavaScript in `frontend/index.html`).
Omdat de twee op een ander adres draaien, laat de API dat uitdrukkelijk toe
met CORS (zie `backend/app/main.py`).

```
.github/workflows/
  ci.yml               CI/CD: tests en images bij elke push, deploy naar Azure bij main
backend/
  app/
    players.py         data: de dataset inladen
    recommender.py     logica: posities, rolprofielen, rolscore, filteren en rangschikken
    main.py            API: de endpoints (FastAPI)
  data/players.json    dataset: één speler per regel
  data/bronnen/        bronbestanden voor het script (niet op GitHub)
  scripts/
    build_dataset.py   bouwt data/players.json opnieuw op
  tests/test_app.py    tests van de logica en de API
  Dockerfile           bouwt de backend-container
  .dockerignore        wat niet in de backend-container moet
  requirements.txt     Python-pakketten die de backend nodig heeft
frontend/
  index.html           het dashboard: HTML met de JavaScript erin
  styles.css           de opmaak
  Dockerfile           bouwt de frontend-container
docs/LOGBOEK-PORTFOLIO.md
docker-compose.yml     start beide containers
.env                   instellingen en geheime sleutels (niet op GitHub)
```

## CI/CD

GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) heeft
twee jobs:

| Job | Wanneer | Wat |
|---|---|---|
| `test-en-build` | Bij elke push, op elke branch | De tests van de backend uitvoeren, beide Docker-images bouwen en opslaan in GitHub Container Registry |
| `deploy` | Alleen bij een push naar `main`, en alleen als `test-en-build` geslaagd is | Inloggen bij Azure en beide Container Apps het nieuwe image geven |

Falen de tests, dan wordt er niets gedeployd en blijft de vorige versie online.

De pipeline logt bij Azure in zonder wachtwoord: Azure vertrouwt alleen pushes
naar `main` van deze repository (een "federatieve referentie" op de beheerde
identiteit `id-github-deploy`). De drie ID's die daarvoor nodig zijn, staan in
de GitHub-secrets van de repository, niet in de code.

Het resultaat staat op GitHub onder het tabblad **Actions**.

## Architectuur op Azure

```
Ontwikkelaar ──push──► GitHub (code)
                          │
                          ▼
                   GitHub Actions
                   1. tests
                   2. images bouwen ──► GitHub Container Registry (ghcr.io)
                   3. deploy (main) ──► Azure
                                          │
   Azure, regio Belgium Central           ▼
   Resourcegroep rg-football-scout
   └── Container Apps-omgeving scout-env
       ├── scout-frontend  (dashboard, poort 8080)
       └── scout-backend   (API, poort 8000)

Gebruiker ──► scout-frontend ──► browser laadt het dashboard
          └─────────────────────► browser vraagt de spelers op bij scout-backend
```

| Onderdeel | Wat |
|---|---|
| Resourcegroep `rg-football-scout` | De "map" met alles van dit project |
| Container Apps-omgeving `scout-env` | De gedeelde omgeving waarin de twee containers draaien |
| Container App `scout-frontend` | Het dashboard, publiek bereikbaar via HTTPS |
| Container App `scout-backend` | De API, publiek bereikbaar via HTTPS (CORS staat open voor het dashboard) |
| Beheerde identiteit `id-github-deploy` | Het account waarmee de pipeline deployt; heeft alleen de rol Inzender op de resourcegroep |
| GitHub Container Registry | Bewaart de Docker-images; de Container Apps halen ze daar op |

## Kosten

- **Azure for Students:** 100 dollar tegoed, zonder kredietkaart. Is het tegoed
  op, dan wordt het abonnement uitgeschakeld in plaats van dat er iets
  aangerekend wordt.
- **Azure Container Apps (verbruiksplan):** elke maand gratis 180.000
  vCPU-seconden, 360.000 GiB-seconden en 2 miljoen verzoeken. Elke container
  gebruikt 0,25 CPU en 0,5 GiB en schaalt naar nul als niemand de app gebruikt.
  Voor dit project blijft het verbruik daardoor binnen het gratis tegoed.
- **Logboeken** worden niet opgeslagen (geen Log Analytics), want dat kost geld
  per GB.
- **GitHub Container Registry:** gratis voor publieke images.
- **Budgetalert:** budget van 5 euro per maand op het abonnement, met een
  e-mail bij 50%, 80% en 100% van de werkelijke kosten.

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

### De dataset opnieuw opbouwen

Dat is alleen nodig als je de data wil aanpassen. De app gebruikt gewoon
`players.json`. Het script heeft deze bronbestanden nodig in
`backend/data/bronnen/` (samen 60 MB, daarom staan ze niet op GitHub):

| Bestand | Waar te halen |
|---|---|
| `ea_fc_26_players.csv` | Uit de zip op [Kaggle](https://www.kaggle.com/datasets/talhademirezen/fc-26-player-stats) (`fc_26_players_stats.csv`, hernoemd) |
| `transfermarkt_players.csv.gz` | [players.csv.gz](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz) |
| `transfermarkt_appearances.csv.gz` | [appearances.csv.gz](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/appearances.csv.gz) |

Het script is een ETL in drie stappen (Extract, Transform, Load) met pandas.
Daarna, in de map `backend`:

```sh
pip install pandas
python scripts/build_dataset.py
```
