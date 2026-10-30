# Portfolio en logboek

Project: Football Scout Recommender · Cloud & Ops 2026-2027

## 1. Het project in het kort

Een recommendation engine voor scouting en spelersrekrutering in het voetbal.
Een club geeft op welk type speler ze zoekt (positie, leeftijd, marktwaarde,
later ook speelstijl en formatie) en krijgt een shortlist van spelers die
passen. In de eindversie kan dat in gewone taal, via een AI-agent. Union
Saint-Gilloise dient als voorbeeldclub.

- Cloudplatform: Microsoft Azure
- Leerpad: Microsoft Certified: Azure Fundamentals (AZ-900)

## 2. Planning

| Milestone | Deadline | Wat moet er werken | Status |
|---|---|---|---|
| Voorstel | 30/09/2026 | Cloudplatform en onderwerp gekozen | Ingediend en goedgekeurd |
| 1. Lokale baseline | 16/10/2026 | App draait lokaal, baseline-recommender, endpoint, propere structuur | Ingediend, demo gegeven |
| 2. Containerisatie en CI | 13/11/2026 | Dockerfile per component, docker-compose, `.env` voor secrets, GitHub Actions bouwt bij elke push | Bezig |
| 3. Cloud deployment en CI/CD | 04/12/2026 | Publieke URL op Azure, push naar `main` deployt automatisch, kostenbeheer | Nog te doen |
| 4. Personalisatie en AI-agent | 18/12/2026 | Aanbevelingen per club, agent verfijnt op basis van input, vergelijking baseline tegenover gepersonaliseerd | Nog te doen |
| Eindpresentatie | Examenperiode | Presentatie voor de jury | Nog te doen |

## 3. Timesheet

Vul per werkmoment in wat gepland was, wat er gebeurd is en hoeveel uren het
kostte.

| Datum | Gepland | Gedaan | Uren |
|---|---|---|---|
| 30/09/2026 | Voorstel indienen | Voorstel ingediend (Azure, scouting-recommender) | 20 minuten |
| 05/10/2026 | Repository opzetten | GitHub-repository aangemaakt met README | 10 minuten |
| 08/10/2026 | Eerste baseline | Eerste versie in Node.js: 12 voorbeeldspelers, rangschikking op doelpunten en assists per wedstrijd | 2 uren en 30 minuten |
| 11/10/2026 | Baseline afwerken | Overgestapt naar Python en FastAPI, echte data gezocht en gekoppeld, rolscore per positie, filters, tests, README, indeling in `backend/` en `frontend/` | 5 uren en 30 minuten |
| 15/10/2026 | Milestone 1 indienen | demo gegeven aan de docent | 20 minuten |
| 20/10/2026 | Start milestone 2: containers en CI | Branch `milestone-2`, een Dockerfile voor backend en frontend, `.dockerignore`, `docker-compose.yml`, `.env.example`, GitHub Actions-workflow, CORS in de backend, README aangepast | 6 uren en 15 minuten |
| 29/10/2026 | Milestone 2 afwerken | Alles nagekeken en enkele kleine aanpassingen, de volledige app gestart vanuit een lege map zonder `.env`, het dashboard getest in de browser. Code verder vereenvoudigd: het datascript is een ETL met pandas die de bronbestanden uit `data/bronnen/` leest, `recommend` geeft één dictionary terug, het dashboard leest de filters met `document.querySelector` | 2 uren en 30 minuten |
| 30/10/2026 | Milestone 2 afronden | Feedback op milestone 1 verwerkt (de code goed kunnen uitleggen). Laatste controle: de repo van GitHub gecloned en met één commando gestart, geen secrets in de repo. Uitleg over pytest en `assert` toegevoegd in de tests. Logboek aangevuld (wat moeilijk en vlot ging, reflectie). Minder bestanden: JavaScript in `index.html`, rolprofielen in `recommender.py`, tests in `test_app.py` | 2 uren |

## 4. Technische keuzes

| Keuze | Alternatief | Waarom deze keuze |
|---|---|---|
| Microsoft Azure | AWS, Google Cloud | Sluit aan op het gekozen leerpad (AZ-900) en er zijn studentencredits. |
| Python met FastAPI | Node.js (eerste versie) | Python is toegelaten in het AI-vak en heeft de meeste bibliotheken voor de personalisatie in Milestone 4. FastAPI lijkt op Express (een functie per endpoint) en maakt zelf API-documentatie op `/docs`. De parameters controleer ik zelf met `if`-regels. |
| Uvicorn als webserver | Geen | FastAPI beschrijft alleen de endpoints; uvicorn ontvangt de verzoeken en geeft ze door. |
| Data in één JSON-bestand in de repository | Databank | Voor 4.244 spelers is een bestand voldoende en het project blijft werken zonder externe diensten. Een databank kan later nog als aparte container. |
| Rolscore als gewogen gemiddelde per positie | Eén score voor iedereen (bv. doelpunten en assists) | De eerste versie beoordeelde alleen aanvallers eerlijk. Met een rolprofiel per positie telt voor elke rol wat daar belangrijk is. De gewichten staan apart bovenaan `recommender.py`, zodat ze in Milestone 4 per club kunnen verschillen. |
| Filters als queryparameters op één endpoint | Aparte endpoints per filter | De AI-agent kan later hetzelfde endpoint aanroepen met de filters die hij uit een zin haalt. |
| Indeling in `backend/` en `frontend/` | Alles in één map | Elk deel wordt in Milestone 2 een eigen container. |
| Twee containers: `backend` en `frontend` (Milestone 2) | Eén container die alles doet | De opdracht vraagt de app op te splitsen in logische componenten. Zo heeft elk deel zijn eigen Dockerfile, net zoals in het DevOps-vak. Beide staan in één repository en `docker-compose.yml` start ze samen. |
| `docker-compose.yml` | Elke container apart starten met `docker build` en `docker run` | Eén kort commando (`docker compose up --build`) start beide containers in de juiste volgorde, en compose leest de instellingen uit `.env`. |
| `python:3.13-slim` als basis voor beide containers | Volledige Python-image | Kleiner: sneller te bouwen en straks goedkoper om naar Azure te sturen. Een vaste versie (3.13) zorgt dat de build later hetzelfde resultaat geeft. |
| `.dockerignore` in de backend | Alles kopiëren | De bronbestanden (60 MB), de tests en het datascript zijn niet nodig om de API te laten draaien. |
| Het datascript als ETL met pandas (Extract, Transform, Load) | Zelf lussen schrijven over de CSV-bestanden | Zo heb ik het geleerd in Data Engineering en Data Science Fundamentals: `read_csv`, filteren, `groupby` om op te tellen en `merge` om de twee bronnen te koppelen. pandas is alleen nodig voor het script, niet voor de app zelf. |
| Het datascript leest de bronbestanden uit een map (`data/bronnen/`) in plaats van ze zelf te downloaden | Automatisch downloaden in het script | Ik bewaar de bronbestanden zelf, zodat het project blijft werken als de downloadlinks verdwijnen. Zonder downloadcode is het script ook veel korter en eenvoudiger: alleen inlezen, koppelen en wegschrijven. |
| Code zo schrijven dat ze lijkt op wat ik in JavaScript en C# gezien heb | Typische Python-schrijfwijzen | Python ken ik vooral uit notebooks (pandas, scikit-learn); een webapp schreef ik tot nu toe in JavaScript. Zo kan ik elke regel uitleggen. Bv. `recommend` geeft één dictionary terug in plaats van twee waarden tegelijk, en het dashboard leest de filters met `document.querySelector`. |
| De poort van het dashboard in `.env`, met een standaardwaarde in `docker-compose.yml` | `.env` verplicht maken | `git clone` plus één commando moet volstaan, ook zonder `.env`. Wie een andere poort nodig heeft, past ze aan in `.env`. Er zijn nog geen geheime sleutels: lokaal bouwen en de pipeline hebben er geen nodig. De eerste komen in Milestone 3 (toegang tot Azure, als GitHub-secret) en Milestone 4 (sleutel van de AI-agent, in `.env`). |
| GitHub Actions bij elke push op elke branch | Alleen op `main` | De opdracht vraagt een build bij elke push. Zo wordt ook het werk op `milestone-2` gecontroleerd voor het naar `main` gaat. |

### De keuze van de data

De data was de moeilijkste keuze. Er zijn drie opties geprobeerd:

1. **StatsBomb Open Data.** Heel gedetailleerde wedstrijddata, maar volledige
   competities zijn er alleen voor seizoen 2015/2016, er zit geen leeftijd of
   marktwaarde in en de ruwe data mag niet in een publieke repository.
2. **Alleen Transfermarkt.** Actueel (seizoen 2025/2026) en met marktwaarde,
   maar per speler zijn er enkel minuten, doelpunten, assists en kaarten.
   Verdedigers en doelmannen konden daardoor alleen op ploegcijfers
   beoordeeld worden, zodat een goede verdediger bij een zwakke ploeg te laag
   scoorde.
3. **EA Sports FC 26 samen met Transfermarkt (gekozen).** EA levert per
   speler individuele eigenschappen van 0 tot 100 voor elke positie.
   Transfermarkt levert marktwaarde, leeftijd, club en de echte
   seizoenscijfers.

Gratis en actuele wedstrijdstatistieken met verdedigende cijfers bleken niet
beschikbaar: FBref heeft zijn geavanceerde statistieken in januari 2026
verwijderd en Sofascore laat geen automatische toegang toe.

Bekende beperkingen van de gekozen data:

- De eigenschappen zijn inschattingen van EA Sports, geen gemeten
  wedstrijdstatistieken.
- De twee bronnen worden gekoppeld op naam en leeftijd. Dat lukt voor 4.244
  van de 5.855 spelers; wie anders gespeld is, ontbreekt.
- 13 competities. De Russische competitie zit niet in EA FC; Griekenland en
  Oekraïne zijn maar gedeeltelijk gedekt.
- De Transfermarkt-dataset wordt sinds juli 2026 niet meer bijgewerkt. De
  bronbestanden zijn daarom lokaal bewaard.

## 5. Waar liep het vast, wat ging vlot

### Milestone 1

**Wat vond ik moeilijk?**
De opstart: van het idee naar een echte baseline gaan. Ik wilde in Milestone 1
al tonen wat de bedoeling van het eindproduct is, terwijl er nog geen AI-agent
en geen personalisatie per club is.

**Wat ging vlot?**

- De codestructuur opzetten, zoals we dat eerder in de opleiding geleerd
  hebben.
- Een eenvoudige frontend maken met filters. Die toont al duidelijk wat later
  met de AI-agent en de personalisatie mogelijk wordt.
- De documentatie: beschrijven wat er gebeurt en hoe.

**Technische problemen en hoe ze opgelost zijn:**

| Probleem | Oplossing |
|---|---|
| De eerste baseline (doelpunten en assists) zette doelmannen en verdedigers altijd onderaan. | Rolprofiel per positie. |
| Geen enkele gratis bron had tegelijk actuele data, marktwaarde en individuele cijfers voor elke positie. | Twee bronnen combineren (zie punt 4). |
| Het downloaden van de bronbestanden vanuit Python bleef minutenlang hangen. | Het netwerk ondersteunt geen IPv6 en Python probeerde die adressen eerst. Opgelost met een aanpassing in het script; in Milestone 2 is het downloaden helemaal uit het script gehaald (zie punt 4). |
| Namen zijn in de twee bronnen soms anders gespeld. | Namen worden vergeleken zonder accenten en hoofdletters, samen met de leeftijd. Een ruimere regel gaf foute koppelingen en is niet gebruikt. |
| Bij doelmannen staan de keeperseigenschappen in het EA-bestand in andere kolommen. | Aparte kolomtoewijzing voor doelmannen in het script. |

### Milestone 2

**Wat vond ik moeilijk?**
Opnieuw uitzoeken hoe Dockerfiles werken, en vooral hoe je met secrets omgaat:
die mogen nooit op GitHub terechtkomen. Op dit moment zijn er nog geen
secrets, wat het eenvoudiger maakte. De aanpak staat wel al klaar met `.env`
en `.env.example`.

**Wat ging vlot?**

- Eens ik vertrokken was liep het vlot, ook de pipeline met GitHub Actions.
- Ik heb mijn project van het vak DevOps opnieuw bekeken om te zien hoe alles
  werkte en hoe ik het hier het best kon toepassen.
- De Dockerfiles zijn niet te complex gemaakt, maar wel volledig in orde.

**Technische problemen en hoe ze opgelost zijn:**

| Probleem | Oplossing |
|---|---|
| In Milestone 1 serveerde de backend ook het dashboard. In een aparte container kan dat niet meer. | De backend serveert alleen nog de API; het dashboard heeft een eigen container. |
| Het dashboard en de API draaien op een ander adres (poort 8080 en 8000). Een browser blokkeert dan standaard de verzoeken van het dashboard naar de API. | CORS ingesteld in de backend, zodat de API verzoeken van het dashboard toelaat. Er is een test die dat controleert. |

## 6. Leerpad en certificaat

Microsoft Certified: Azure Fundamentals (AZ-900).

- Stand van zaken: _in te vullen vanwege wachten op extra info docent_
- Bewijs: _certificaat of screenshots toevoegen_

## 7. Reflectie op het leerproces

Per milestone: wat heb ik geleerd, wat zou ik anders doen en wat neem ik mee
naar de volgende milestone?

### Milestone 1

**Wat heb ik geleerd?**
Hoe je met een baseline duidelijk kan tonen wat je idee is en waar je met het
project naartoe wil. Daarnaast heb ik leren werken met Visual Studio Code.

**Wat zou ik anders doen?**
Dat kan ik in deze fase nog niet echt zeggen: ik heb het gevoel dat ik alles
doe zoals ik het wil. Het was wel even zoeken naar hoe ik mijn idee kon tonen.
Ik wilde geen simpele recommender op basis van bijvoorbeeld doelpunten en
assists, maar voor elke positie kijken naar de eigenschappen die daar
belangrijk zijn en daarop filteren. Later komen daar complexere filters bij
via de personalisatie en de AI-agent.

**Wat neem ik mee naar de volgende milestone?**
Verder bouwen op wat er staat, en vanuit de indeling in backend en frontend
een goede structuur opzetten voor de pipeline en Docker.

### Milestone 2

**Wat heb ik geleerd?**
Docker en docker-compose toepassen zodat het volledige project met 1 commando start.

**Wat zou ik anders doen?**
Net zoals bij de vorige milestone zou ik niet meteen iets anders doen: deze
milestone was vooral nog steeds het opzetten van het project. In de volgende milestones
wil ik verder gaan met de personalisatie om tot een mooier geheel te komen.

**Wat neem ik mee naar de volgende milestone?**
De duidelijke structuur behouden en op die manier verder bouwen, zodat de app
naar de cloud kan.
