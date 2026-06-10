"""
Writes the one-line summary and assigns subgroup tags for a paper.

The LLM provider is swappable (free tiers): "github" (GitHub Models, the
default, uses your repo token), "gemini" (Google AI Studio), or "groq".
Set the LLM_PROVIDER environment variable to switch. If a provider's free
tier ever changes, you can move to another without touching anything else.
"""

import json
import re
import requests

import config


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
def _taxonomy_block():
    return "\n".join(f"- {c['key']}: {c['label']} ({c['hint']})" for c in config.TAXONOMY)


def build_prompt(paper):
    first_author = paper["authors"][0].split()[-1] if paper["authors"] else "The authors"
    abstract = paper["abstract"] or "(no abstract available)"

    user = f"""You are cataloguing a research paper for a microtransit / demand-responsive transit / carsharing literature database.

TITLE: {paper['title']}
FIRST AUTHOR SURNAME: {first_author}
JOURNAL: {paper['journal'] or 'unknown'}
YEAR: {paper['year'] or 'unknown'}
ABSTRACT: {abstract}

TASK 1 - SUMMARY
Write ONE sentence in this shape:
"<surname> et al. conducted a study [in/at <location> if stated] focusing on <topic> using <method> and find that <main finding>."
{config.SUMMARY_STYLE}

TASK 2 - TAGS
Choose every category that genuinely applies (usually 1-3) from this list:
{_taxonomy_block()}

Return ONLY valid JSON, no commentary, no code fences:
{{"summary": "<one sentence>", "tags": ["key1", "key2"]}}"""

    return [
        {"role": "system", "content": "You are a precise academic cataloguer. You never invent facts not present in the source text."},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# Provider calls
# ---------------------------------------------------------------------------
def _model_name():
    return config.LLM_MODEL or config.DEFAULT_MODELS[config.LLM_PROVIDER]


def _call_github(messages):
    token = config.GITHUB_MODELS_TOKEN
    if not token:
        raise RuntimeError("GITHUB_MODELS_TOKEN is not set.")
    resp = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"model": _model_name(), "messages": messages, "temperature": 0.2},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(messages):
    key = config.GEMINI_API_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    # Fold the system + user messages into one prompt for Gemini's REST API.
    text = "\n\n".join(m["content"] for m in messages)
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{_model_name()}:generateContent?key={key}")
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": text}]}],
              "generationConfig": {"temperature": 0.2}},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_groq(messages):
    key = config.GROQ_API_KEY
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": _model_name(), "messages": messages, "temperature": 0.2},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


_PROVIDERS = {"github": _call_github, "gemini": _call_gemini, "groq": _call_groq}


def call_llm(messages):
    provider = config.LLM_PROVIDER
    if provider not in _PROVIDERS:
        raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")
    return _PROVIDERS[provider](messages)


# ---------------------------------------------------------------------------
# Parsing + public entry point
# ---------------------------------------------------------------------------
def parse_result(text):
    """Pull the JSON object out of the model's reply, tolerating stray text."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model reply.")
    data = json.loads(match.group(0))
    summary = (data.get("summary") or "").strip()
    tags = [t for t in (data.get("tags") or []) if t in config.VALID_TAGS]
    return summary, tags


def _fallback(paper):
    """Used when there is no abstract to work from -> metadata-only line."""
    surname = paper["authors"][0].split()[-1] if paper["authors"] else "The authors"
    title = paper["title"].rstrip(".")
    return f"{surname} et al. published \"{title}\" (abstract unavailable; summary pending)."


def summarize_paper(paper):
    """Return the paper dict with `summary`, `tags`, and `needs_review` added."""
    if not paper["abstract"] or len(paper["abstract"]) < 40:
        paper["summary"] = _fallback(paper)
        paper["tags"] = []
        paper["needs_review"] = True
        return paper
    try:
        summary, tags = parse_result(call_llm(build_prompt(paper)))
        paper["summary"] = summary or _fallback(paper)
        paper["tags"] = tags
        paper["needs_review"] = not bool(summary)
    except Exception as exc:  # noqa: BLE001  (we want the run to continue)
        print(f"    ! summary failed: {exc}")
        paper["summary"] = _fallback(paper)
        paper["tags"] = []
        paper["needs_review"] = True
    return paper
