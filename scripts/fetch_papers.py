"""
Fetches candidate papers from OpenAlex.

OpenAlex is a free, open scholarly index (no API key needed) that covers
essentially all journals and includes abstracts. This module turns raw
OpenAlex records into clean, uniform dictionaries the rest of the pipeline
can use.
"""

import time
import requests

import config

OPENALEX_WORKS = "https://api.openalex.org/works"

# Only ask OpenAlex for the fields we actually use -> smaller, faster responses.
SELECT_FIELDS = ",".join([
    "id", "doi", "title", "publication_year",
    "authorships", "primary_location", "abstract_inverted_index",
    "type",
])


def reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as {word: [positions]}. Rebuild the text."""
    if not inverted_index:
        return ""
    positions = []
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort(key=lambda p: p[0])
    return " ".join(word for _, word in positions)


def _normalise(record):
    """Turn one raw OpenAlex work into the shape we store."""
    authorships = record.get("authorships") or []
    authors = [
        a.get("author", {}).get("display_name", "").strip()
        for a in authorships
        if a.get("author", {}).get("display_name")
    ]

    loc = record.get("primary_location") or {}
    source = (loc.get("source") or {})
    journal = source.get("display_name") or ""

    doi = record.get("doi") or ""
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]

    return {
        "id": record.get("id", ""),                       # OpenAlex URL id (unique)
        "doi": doi,
        "title": (record.get("title") or "").strip(),
        "year": record.get("publication_year"),
        "journal": journal,
        "authors": authors,
        "abstract": reconstruct_abstract(record.get("abstract_inverted_index")),
        "url": loc.get("landing_page_url") or record.get("id", ""),
    }


def _fetch_one_query(query, mailto):
    """Page through all results for a single search phrase."""
    results = []
    cursor = "*"
    base_params = {
        "search": query,
        "filter": (
            f"from_publication_date:{config.YEAR_FROM}-01-01,"
            f"to_publication_date:{config.YEAR_TO}-12-31,"
            "type:article"
        ),
        "select": SELECT_FIELDS,
        "per-page": 200,
    }
    if mailto:
        base_params["mailto"] = mailto

    while cursor:
        params = dict(base_params, cursor=cursor)
        resp = requests.get(OPENALEX_WORKS, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        for rec in payload.get("results", []):
            if rec.get("title"):
                results.append(_normalise(rec))
        cursor = payload.get("meta", {}).get("next_cursor")
        time.sleep(0.2)  # be polite to a free service
    return results


def fetch_candidates():
    """Run every search phrase, merge results, drop duplicates by OpenAlex id."""
    seen = {}
    for query in config.SEARCH_QUERIES:
        try:
            for paper in _fetch_one_query(query, config.OPENALEX_MAILTO):
                if paper["id"] and paper["id"] not in seen:
                    seen[paper["id"]] = paper
        except requests.RequestException as exc:
            print(f"  ! query failed ({query!r}): {exc}")
    return list(seen.values())


if __name__ == "__main__":
    # Quick manual check (needs network access to OpenAlex).
    found = fetch_candidates()
    print(f"Fetched {len(found)} unique candidate papers.")
    for p in found[:3]:
        print("-", p["year"], p["title"][:80])
