const playerGrid = document.querySelector("#players");
const message = document.querySelector("#message");
const resultCount = document.querySelector("#result-count");
const filters = document.querySelector("#filters");

const euroFormatter = new Intl.NumberFormat("nl-BE", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

function addTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderBreakdown(player) {
  const list = document.createElement("ul");
  list.className = "breakdown";
  for (const item of player.score_breakdown) {
    const row = document.createElement("li");
    addTextElement(row, "span", "breakdown-label", item.label);
    const bar = addTextElement(row, "span", "breakdown-bar", "");
    bar.style.setProperty("--value", `${item.value}%`);
    addTextElement(row, "span", "breakdown-value", item.value);
    list.append(row);
  }
  return list;
}

function renderPlayer(player, index) {
  const card = document.createElement("article");
  card.className = "player-card";

  const cardTop = document.createElement("div");
  cardTop.className = "card-top";
  addTextElement(cardTop, "span", "rank", String(index + 1).padStart(2, "0"));
  addTextElement(cardTop, "span", "position", player.position_label);
  card.append(cardTop);

  addTextElement(card, "h3", "player-name", player.name);
  addTextElement(card, "p", "club", `${player.club} · ${player.league}`);

  const details = document.createElement("dl");
  details.className = "player-details";
  for (const [label, value] of [
    ["Rolscore", `${player.score.toFixed(1)} / 100`],
    ["Leeftijd", `${player.age} jaar`],
    ["Marktwaarde", euroFormatter.format(player.market_value_eur)],
    ["Seizoen", `${player.minutes} min · ${player.goals} G · ${player.assists} A`],
  ]) {
    const detail = document.createElement("div");
    addTextElement(detail, "dt", "", label);
    addTextElement(detail, "dd", "", value);
    details.append(detail);
  }
  card.append(details);

  addTextElement(card, "p", "breakdown-title", "Opbouw van de rolscore");
  card.append(renderBreakdown(player));

  return card;
}

function buildQuery() {
  const form = new FormData(filters);
  const query = new URLSearchParams({ limit: "12" });
  for (const name of ["position", "league", "max_age", "min_minutes"]) {
    if (form.get(name) !== "") {
      query.set(name, form.get(name));
    }
  }
  if (form.get("max_market_value_millions") !== "") {
    query.set(
      "max_market_value",
      String(Math.round(Number(form.get("max_market_value_millions")) * 1_000_000)),
    );
  }
  return query;
}

async function fetchJson(url) {
  const response = await fetch(url);
  const result = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(result.detail)
      ? result.detail.map((item) => item.msg).join("; ")
      : result.detail;
    throw new Error(detail ?? `Verzoek mislukt (${response.status}).`);
  }
  return result;
}

async function loadRecommendations() {
  try {
    const result = await fetchJson(`/api/recommendations?${buildQuery()}`);

    playerGrid.replaceChildren(
      ...result.recommendations.map((player, index) =>
        renderPlayer(player, index),
      ),
    );
    resultCount.textContent = `${result.count} van ${result.total_matching} spelers`;
    message.textContent =
      result.count === 0 ? "Geen spelers voldoen aan deze filters." : "";
    message.classList.toggle("is-hidden", result.count > 0);
  } catch (error) {
    playerGrid.replaceChildren();
    resultCount.textContent = "";
    message.textContent = `Aanbevelingen konden niet worden geladen: ${error.message}`;
    message.classList.remove("is-hidden");
  }
}

async function loadFilterOptions() {
  const options = await fetchJson("/api/options");
  for (const [code, label] of Object.entries(options.positions)) {
    filters.elements.position.add(new Option(label, code));
  }
  for (const league of options.leagues) {
    filters.elements.league.add(new Option(league, league));
  }
}

filters.addEventListener("input", loadRecommendations);
filters.addEventListener("submit", (event) => event.preventDefault());

loadFilterOptions().catch(() => {});
loadRecommendations();
