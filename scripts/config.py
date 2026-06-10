"""
Central configuration for the literature tracker.

Edit this file to change what gets collected and how it is organised.
Nothing else needs to be touched for normal use.
"""

import os

# ----------------------------------------------------------------------------
# 1. WHAT TO SEARCH FOR
# ----------------------------------------------------------------------------
# Each entry is a phrase searched across paper titles + abstracts on OpenAlex.
# Phrases are matched loosely (word order tolerant). Add or remove freely.
SEARCH_QUERIES = [
    "microtransit",
    "micro-transit",
    "on-demand transit",
    "on-demand public transport",
    "demand-responsive transit",
    "demand responsive transport",
    "flexible transit service",
    "ride-pooling transit",
    "carsharing",
    "car sharing",
    "car-sharing",
]

# Only keep papers published within this window (inclusive).
YEAR_FROM = 2020
YEAR_TO = 2026

# ----------------------------------------------------------------------------
# 2. SUBGROUP TAXONOMY  (the "route lines")
# ----------------------------------------------------------------------------
# key:   stable id stored in the data + used by the website filters
# label: shown to the reader
# color: the route-line colour on the website (metro-map style)
# hint:  one line that tells the summariser what belongs in this category
TAXONOMY = [
    {"key": "operations",  "label": "Operations",                 "color": "#DA3E32",
     "hint": "routing, dispatching, fleet sizing, vehicle repositioning, real-time optimisation"},
    {"key": "planning",    "label": "Planning & service design",  "color": "#2B6CB0",
     "hint": "where/whether to deploy, network design, feasibility, service area design"},
    {"key": "fmlm",        "label": "First/last mile",            "color": "#6B46C1",
     "hint": "feeder service, integration with fixed-route transit, first-mile/last-mile connection"},
    {"key": "demand",      "label": "Demand & ridership",         "color": "#2F855A",
     "hint": "who rides and why, mode choice, adoption, ridership patterns, user identification"},
    {"key": "equity",      "label": "Equity & accessibility",     "color": "#D53F8C",
     "hint": "underserved groups, affordability, ADA/accessibility, digital divide, spatial equity"},
    {"key": "technology",  "label": "Technology & platforms",     "color": "#0987A0",
     "hint": "booking apps, matching algorithms, MaaS integration, data systems"},
    {"key": "policy",      "label": "Policy, pricing & regulation","color": "#B7791F",
     "hint": "fares, subsidies, governance, contracting, regulation, business models"},
    {"key": "environment", "label": "Environmental & sustainability","color": "#557C3E",
     "hint": "emissions, VMT effects, energy use, electrification impacts"},
    {"key": "evaluation",  "label": "Evaluation & performance",   "color": "#4A5568",
     "hint": "before/after studies, ridership & cost metrics, reliability, impact assessment"},
    {"key": "covid",       "label": "COVID-19 impacts",           "color": "#9C4221",
     "hint": "pandemic-era service changes, ridership disruption, recovery"},
    {"key": "carsharing",  "label": "Carsharing",                 "color": "#1A365D",
     "hint": "station-based or free-floating carsharing, EV carsharing, car-share membership"},
]

VALID_TAGS = {c["key"] for c in TAXONOMY}

# ----------------------------------------------------------------------------
# 3. SUMMARY STYLE
# ----------------------------------------------------------------------------
# Plain-language guidance handed to the summariser. Tuned to a concise,
# associations-not-causation academic voice.
SUMMARY_STYLE = (
    "Use British English spelling. Write in the past tense. Be concise. "
    "Present findings as associations or observations, never as causal claims. "
    "Do not invent details: if the abstract does not state a location or method, "
    "omit that clause rather than guessing."
)

# ----------------------------------------------------------------------------
# 4. RUNTIME SETTINGS (usually controlled by environment variables)
# ----------------------------------------------------------------------------
# OpenAlex asks for a contact email to use its fast "polite pool". Set the
# OPENALEX_MAILTO repository variable to your email. It is never published.
OPENALEX_MAILTO = os.environ.get("OPENALEX_MAILTO", "")

# Which free LLM provider writes the summaries: "github", "gemini", or "groq".
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "github").lower()

# Default model per provider. Override with the LLM_MODEL env var if desired.
DEFAULT_MODELS = {
    "github": "openai/gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "groq":   "llama-3.3-70b-versatile",
}
LLM_MODEL = os.environ.get("LLM_MODEL", "")  # blank -> use the default above

# Tokens / keys (set as repository secrets, never hard-coded here).
GITHUB_MODELS_TOKEN = os.environ.get("GITHUB_MODELS_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Throttling to stay inside free rate limits.
# Cap on how many NEW papers are summarised per run (protects the backfill).
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "40"))
# Seconds to wait between summary calls.
SECONDS_BETWEEN_CALLS = float(os.environ.get("SECONDS_BETWEEN_CALLS", "4"))

# Where the database lives.
DATA_FILE = os.environ.get(
    "DATA_FILE",
    os.path.join(os.path.dirname(__file__), "..", "data", "papers.json"),
)
