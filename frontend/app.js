// De elementen uit index.html die we nodig hebben.
const playerGrid = document.querySelector("#players");
const message = document.querySelector("#message");
const resultCount = document.querySelector("#result-count");
const filters = document.querySelector("#filters");

// Zet een bedrag om naar een korte notatie, bv. 5000000 -> "€ 5 mln.".
const euroFormatter = new Intl.NumberFormat("nl-BE", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

// Maakt een HTML-element met tekst en hangt het aan een ander element.
function addTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

// Voegt één regel toe aan de details van een speler, bv. "Leeftijd: 22 jaar".
function addDetail(details, label, value) {
  const detail = document.createElement("div");
  addTextElement(detail, "dt", "", label);
  addTextElement(detail, "dd", "", value);
  details.append(detail);
}

// Maakt de balkjes die tonen hoe de rolscore is opgebouwd.
function renderBreakdown(player) {
  const list = document.createElement("ul");
  list.className = "breakdown";

  for (const item of player.score_breakdown) {
    const row = document.createElement("li");
    addTextElement(row, "span", "breakdown-label", item.label);
    const bar = addTextElement(row, "span", "breakdown-bar", "");
    // De breedte van het balkje staat in de CSS-variabele --value.
    bar.style.setProperty("--value", item.value + "%");
    addTextElement(row, "span", "breakdown-value", item.value);
    list.append(row);
  }

  return list;
}

// Maakt de kaart van één speler.
function renderPlayer(player, rank) {
  const card = document.createElement("article");
  card.className = "player-card";

  // Bovenaan: het rangnummer (01, 02, ...) en de positie.
  const cardTop = document.createElement("div");
  cardTop.className = "card-top";
  addTextElement(cardTop, "span", "rank", String(rank).padStart(2, "0"));
  addTextElement(cardTop, "span", "position", player.position_label);
  card.append(cardTop);

  addTextElement(card, "h3", "player-name", player.name);
  addTextElement(card, "p", "club", player.club + " · " + player.league);

  const details = document.createElement("dl");
  details.className = "player-details";
  addDetail(details, "Rolscore", player.score.toFixed(1) + " / 100");
  addDetail(details, "Leeftijd", player.age + " jaar");
  addDetail(details, "Marktwaarde", euroFormatter.format(player.market_value_eur));
  addDetail(
    details,
    "Seizoen",
    player.minutes + " min · " + player.goals + " G · " + player.assists + " A",
  );
  card.append(details);

  addTextElement(card, "p", "breakdown-title", "Opbouw van de rolscore");
  card.append(renderBreakdown(player));

  return card;
}

// Bouwt de URL voor de API op basis van de ingevulde filters.
function buildUrl() {
  const form = new FormData(filters);
  let url = "/api/recommendations?limit=12";

  // Deze filters gaan ongewijzigd naar de API, als ze ingevuld zijn.
  const names = ["position", "league", "max_age", "min_minutes"];
  for (const name of names) {
    const value = form.get(name);
    if (value !== "") {
      url = url + "&" + name + "=" + encodeURIComponent(value);
    }
  }

  // De marktwaarde wordt ingevuld in miljoen euro, de API verwacht euro.
  const millions = form.get("max_market_value_millions");
  if (millions !== "") {
    const euros = Math.round(Number(millions) * 1000000);
    url = url + "&max_market_value=" + euros;
  }

  return url;
}

// Haalt gegevens op van de API. Bij een fout gooien we de foutmelding op.
async function fetchJson(url) {
  const response = await fetch(url);
  const result = await response.json();

  if (!response.ok) {
    let errorText = "Verzoek mislukt (" + response.status + ").";
    if (typeof result.detail === "string") {
      errorText = result.detail;
    }
    throw new Error(errorText);
  }

  return result;
}

// Haalt de aanbevelingen op en toont ze op de pagina.
async function loadRecommendations() {
  try {
    const result = await fetchJson(buildUrl());

    // Oude kaarten weghalen en de nieuwe toevoegen.
    playerGrid.replaceChildren();
    let rank = 1;
    for (const player of result.recommendations) {
      playerGrid.append(renderPlayer(player, rank));
      rank = rank + 1;
    }

    resultCount.textContent = result.count + " van " + result.total_matching + " spelers";

    if (result.count === 0) {
      message.textContent = "Geen spelers voldoen aan deze filters.";
      message.classList.remove("is-hidden");
    } else {
      message.textContent = "";
      message.classList.add("is-hidden");
    }
  } catch (error) {
    playerGrid.replaceChildren();
    resultCount.textContent = "";
    message.textContent = "Aanbevelingen konden niet worden geladen: " + error.message;
    message.classList.remove("is-hidden");
  }
}

// Vult de keuzelijsten voor positie en competitie.
async function loadFilterOptions() {
  const options = await fetchJson("/api/options");

  for (const code in options.positions) {
    const label = options.positions[code];
    filters.elements.position.add(new Option(label, code));
  }

  for (const league of options.leagues) {
    filters.elements.league.add(new Option(league, league));
  }
}

// Bij elke wijziging van een filter halen we nieuwe aanbevelingen op.
filters.addEventListener("input", loadRecommendations);

// Enter in een invulveld mag de pagina niet herladen.
filters.addEventListener("submit", function (event) {
  event.preventDefault();
});

loadFilterOptions();
loadRecommendations();
