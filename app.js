/* Microtransit literature tracker — front-end logic (no framework, no build) */

/* Category definitions. Keep in sync with scripts/config.py TAXONOMY.
   (It changes rarely; only edit if you add/rename a subgroup.) */
const TAXONOMY = [
  { key: "operations",  label: "Operations",                  color: "#DA3E32" },
  { key: "planning",    label: "Planning & service design",   color: "#2B6CB0" },
  { key: "fmlm",        label: "First/last mile",             color: "#6B46C1" },
  { key: "demand",      label: "Demand & ridership",          color: "#2F855A" },
  { key: "equity",      label: "Equity & accessibility",      color: "#D53F8C" },
  { key: "technology",  label: "Technology & platforms",      color: "#0987A0" },
  { key: "policy",      label: "Policy, pricing & regulation","color": "#B7791F" },
  { key: "environment", label: "Environmental & sustainability","color": "#557C3E" },
  { key: "evaluation",  label: "Evaluation & performance",    color: "#4A5568" },
  { key: "covid",       label: "COVID-19 impacts",            color: "#9C4221" },
  { key: "carsharing",  label: "Carsharing",                  color: "#1A365D" },
];
const TAX = Object.fromEntries(TAXONOMY.map((t) => [t.key, t]));

const state = { papers: [], query: "", tags: new Set(), sort: "year-desc" };

const el = (id) => document.getElementById(id);

/* ---- Load ---------------------------------------------------------- */
async function load() {
  try {
    const res = await fetch("data/papers.json", { cache: "no-store" });
    if (!res.ok) throw new Error("no data file");
    const data = await res.json();
    if (!data.papers || !data.papers.length) throw new Error("empty");
    init(data);
  } catch {
    init(window.__SAMPLE__, true); // fall back to the inline preview data
  }
}

function init(data, isSample = false) {
  state.papers = data.papers;
  el("meta-count").textContent = data.papers.length;
  el("meta-updated").textContent = isSample ? "preview" : (data.updated_at || "—");
  el("sample-banner").hidden = !isSample && !data.papers.some((p) => p.sample);
  buildRouteline();
  buildLines();
  bindControls();
  render();
}

/* ---- Signature route line ----------------------------------------- */
function buildRouteline() {
  el("routeline").innerHTML = TAXONOMY
    .map((t) => `<span class="routeline__seg" style="background:${t.color}"></span>`)
    .join("");
}

/* ---- Filter chips -------------------------------------------------- */
function buildLines() {
  const counts = {};
  state.papers.forEach((p) => (p.tags || []).forEach((k) => (counts[k] = (counts[k] || 0) + 1)));

  const chips = TAXONOMY.map((t) => {
    const n = counts[t.key] || 0;
    return `<button class="line" data-key="${t.key}" aria-pressed="false"
              style="--c:${t.color}">
              <span class="line__dot"></span>${t.label}
              <span class="line__n">${n}</span>
            </button>`;
  }).join("");

  el("lines").innerHTML =
    chips + `<button class="lines__clear" id="clear" hidden>Clear filters</button>`;

  el("lines").querySelectorAll(".line").forEach((btn) =>
    btn.addEventListener("click", () => toggleTag(btn.dataset.key))
  );
  el("clear").addEventListener("click", () => {
    state.tags.clear();
    syncLineButtons();
    render();
  });
}

function toggleTag(key) {
  state.tags.has(key) ? state.tags.delete(key) : state.tags.add(key);
  syncLineButtons();
  render();
}

function syncLineButtons() {
  el("lines").querySelectorAll(".line").forEach((btn) =>
    btn.setAttribute("aria-pressed", state.tags.has(btn.dataset.key) ? "true" : "false")
  );
  el("clear").hidden = state.tags.size === 0;
}

/* ---- Controls ------------------------------------------------------ */
function bindControls() {
  el("search").addEventListener("input", (e) => {
    state.query = e.target.value.toLowerCase().trim();
    render();
  });
  el("sort").addEventListener("change", (e) => {
    state.sort = e.target.value;
    render();
  });
}

/* ---- Filtering + sorting ------------------------------------------ */
function visiblePapers() {
  let list = state.papers;

  if (state.tags.size) {
    list = list.filter((p) => (p.tags || []).some((k) => state.tags.has(k)));
  }
  if (state.query) {
    const q = state.query;
    list = list.filter((p) =>
      [p.title, p.summary, p.journal, (p.authors || []).join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }

  const sorters = {
    "year-desc": (a, b) => (b.year || 0) - (a.year || 0),
    "year-asc": (a, b) => (a.year || 0) - (b.year || 0),
    title: (a, b) => (a.title || "").localeCompare(b.title || ""),
    added: (a, b) => (b.added_date || "").localeCompare(a.added_date || ""),
  };
  return [...list].sort(sorters[state.sort]);
}

/* ---- Rendering ----------------------------------------------------- */
function authorLine(p) {
  const a = p.authors || [];
  if (!a.length) return "";
  const names = a.length > 3 ? `${a.slice(0, 3).join(", ")}, et al.` : a.join(", ");
  return names;
}

function tagChips(p) {
  return (p.tags || [])
    .filter((k) => TAX[k])
    .map((k) => {
      const t = TAX[k];
      return `<button class="tag" data-key="${k}" style="--c:${t.color}">
                <span class="tag__dot"></span>${t.label}</button>`;
    })
    .join("");
}

function card(p) {
  const primary = (p.tags || []).find((k) => TAX[k]);
  const railColor = primary ? TAX[primary].color : "var(--rail)";
  const byline = [authorLine(p), p.journal ? `<span class="journal">${p.journal}</span>` : ""]
    .filter(Boolean)
    .join(" · ");
  const needs = p.needs_review ? `<span class="card__needs">[check]</span>` : "";
  const titleHtml = p.url && p.url !== "#"
    ? `<a href="${p.url}" target="_blank" rel="noopener">${p.title}</a>`
    : p.title;

  return `<article class="card" style="--card-c:${railColor}">
    <div class="card__head">
      <h2 class="card__title">${titleHtml}</h2>
      <span class="card__year">${p.year || ""}</span>
    </div>
    <p class="card__byline">${byline}</p>
    <p class="card__summary">${p.summary || ""}${needs}</p>
    <div class="tags">${tagChips(p)}</div>
  </article>`;
}

function render() {
  const list = visiblePapers();
  el("count").textContent =
    `${list.length} ${list.length === 1 ? "paper" : "papers"}` +
    (state.tags.size || state.query ? " (filtered)" : "");

  if (!list.length) {
    el("list").innerHTML = "";
    el("empty").hidden = false;
    el("empty").innerHTML =
      `No papers match these filters. <b>Try clearing a route line or your search.</b>`;
    return;
  }
  el("empty").hidden = true;
  el("list").innerHTML = list.map(card).join("");

  // clicking a tag on a card toggles that line filter
  el("list").querySelectorAll(".tag").forEach((btn) =>
    btn.addEventListener("click", () => {
      toggleTag(btn.dataset.key);
      window.scrollTo({ top: 0, behavior: "smooth" });
    })
  );
}

load();
