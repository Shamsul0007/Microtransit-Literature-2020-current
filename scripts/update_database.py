"""
The job that runs on a schedule.

It loads the existing database, asks OpenAlex for matching papers, keeps only
the ones it has never seen, summarises and tags up to MAX_PER_RUN of them
(to stay inside free rate limits), then writes the database back out.

Run locally:   python scripts/update_database.py
On GitHub:     handled automatically by .github/workflows/update.yml
"""

import json
import os
import time
from datetime import datetime, timezone

import config
import fetch_papers
import summarize


def load_database():
    path = os.path.abspath(config.DATA_FILE)
    if not os.path.exists(path):
        return {"updated_at": None, "count": 0, "papers": []}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Ignore any seed/sample rows once real data starts arriving.
    data["papers"] = [p for p in data.get("papers", []) if not p.get("sample")]
    return data


def save_database(papers):
    path = os.path.abspath(config.DATA_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    papers.sort(key=lambda p: (-(p.get("year") or 0), p.get("title", "").lower()))
    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "count": len(papers),
        "papers": papers,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def main():
    print("Loading existing database ...")
    db = load_database()
    existing = db["papers"]
    known_ids = {p["id"] for p in existing if p.get("id")}
    known_dois = {p["doi"] for p in existing if p.get("doi")}
    print(f"  {len(existing)} papers already stored.")

    print("Fetching candidates from OpenAlex ...")
    candidates = fetch_papers.fetch_candidates()
    print(f"  {len(candidates)} candidates returned.")

    new_papers = [
        c for c in candidates
        if c["id"] not in known_ids and (not c["doi"] or c["doi"] not in known_dois)
    ]
    print(f"  {len(new_papers)} are new.")

    to_process = new_papers[: config.MAX_PER_RUN]
    if len(new_papers) > config.MAX_PER_RUN:
        print(f"  Processing {config.MAX_PER_RUN} this run; the rest follow next run.")

    added = []
    for i, paper in enumerate(to_process, 1):
        print(f"  [{i}/{len(to_process)}] {paper['title'][:70]}")
        paper["added_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        added.append(summarize.summarize_paper(paper))
        if i < len(to_process):
            time.sleep(config.SECONDS_BETWEEN_CALLS)

    save_database(existing + added)
    print(f"Done. Added {len(added)} papers; database now holds {len(existing) + len(added)}.")


if __name__ == "__main__":
    main()
