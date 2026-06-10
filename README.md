[README.md](https://github.com/user-attachments/files/28809428/README.md)
# Microtransit & shared-mobility literature tracker

A self-updating website that catalogues research on **microtransit, on-demand /
demand-responsive transit, and carsharing** (2020–2026).

Each week it searches the academic literature for new matching papers, writes a
one-line summary of each in the form *"X et al. conducted a study at Y focusing
on Z using method W and find that…"*, files it under the right subgroups, and
adds it to the site. **No uploads, no manual triggering, no cost.**

---

## How it works

1. **GitHub Actions** runs a script on a schedule (weekly by default).
2. The script asks **OpenAlex** (a free, open scholarly index — no key needed)
   for new papers matching your keywords, and rebuilds their abstracts.
3. A **free LLM** (GitHub Models by default) reads each abstract and writes the
   summary + assigns subgroup tags.
4. The result is saved to `data/papers.json` and committed back to the repo.
5. **GitHub Pages** serves the website, which reads that file. New papers simply
   appear.

Everything runs on a **public** GitHub repo, which is free: unlimited Actions
minutes, free Pages, and GitHub Models within its free tier.

---

## One-time setup (about 10 minutes)

1. **Create a new repository** on a *personal* GitHub account (not the
   university one — institutional accounts can block public repos/Pages and get
   deactivated when you leave). Make it **Public**.
2. **Upload these files** to the repo (drag-and-drop in the browser works, or use
   `git push`). Keep the folder structure intact.
3. **Add your email for OpenAlex** (gets faster, "polite" access):
   repo → **Settings → Secrets and variables → Actions → Variables → New variable**
   → name `OPENALEX_MAILTO`, value your email. (It is never published.)
4. **Enable the website**: repo → **Settings → Pages** → *Source: Deploy from a
   branch* → branch `main`, folder `/ (root)` → Save. Your site appears at
   `https://<your-username>.github.io/<repo-name>/`.
5. **Allow the workflow to write**: repo → **Settings → Actions → General →
   Workflow permissions** → select *Read and write permissions* → Save.
6. **Run it once**: repo → **Actions** tab → *Update literature database* → *Run
   workflow*. Watch it pull and summarise the first batch of papers.

That's it. From now on it runs by itself every Monday.

---

## Filling in 2020–2026 (the backfill)

The first run only processes a capped number of papers (40) so it stays inside
the free LLM rate limits. To load the back-catalogue faster:

- Trigger **Run workflow** a few times (each run picks up where the last left
  off), **or**
- In the run dialog set **max_per_run** higher (e.g. `150`).

Once the backlog is cleared, the weekly schedule keeps it current with almost no
work per run.

---

## Customising it

**Keywords** — edit `SEARCH_QUERIES` in `scripts/config.py`.

**Subgroups (the "route lines")** — edit `TAXONOMY` in `scripts/config.py`.
If you add or rename a category, also update the matching `TAXONOMY` list at the
top of `app.js` so the website shows it (same `key`, `label`, `color`).

**Schedule** — change the `cron` line in `.github/workflows/update.yml`
(`"0 6 * * 1"` = Mondays 06:00 UTC).

**Summary voice** — edit `SUMMARY_STYLE` in `scripts/config.py` (currently:
British English, concise, associations not causal claims).

---

## Switching the free summariser

Default is **GitHub Models**, which works automatically inside the workflow.
If its free tier ever changes, switch providers with one setting — no rebuild:

| Provider | Set `LLM_PROVIDER` to | Free key from |
|----------|----------------------|---------------|
| GitHub Models (default) | `github` | built-in repo token |
| Google Gemini | `gemini` | Google AI Studio → save key as secret `GEMINI_API_KEY` |
| Groq | `groq` | Groq console → save key as secret `GROQ_API_KEY` |

To switch, change `LLM_PROVIDER` in the workflow's `env:` block and add the
relevant secret under **Settings → Secrets and variables → Actions**.

> Note: free LLM tiers send your text to the provider, but you are only ever
> sending **published abstracts**, so there is nothing private at stake here.

---

## Optional: richer summaries from full text

The automatic summaries come from **abstracts**, which usually state the
location, method, and main finding. If for a specific paper you want detail the
abstract doesn't contain (exact sample size, coefficients, etc.), that needs the
full PDF — which paywalls block. For those, summarise them yourself from your
library PDF and add the entry to `data/papers.json` by hand. This is optional;
the system runs fully without it.

---

## Running locally (optional, for testing)

```bash
pip install -r requirements.txt
export OPENALEX_MAILTO="you@example.com"
export LLM_PROVIDER="gemini"           # or groq; github needs a token
export GEMINI_API_KEY="..."            # whichever provider you chose
python scripts/update_database.py
```

Then open `index.html` in a browser.

---

## Files

```
index.html               the website
style.css  app.js         its styling and logic
data/papers.json          the catalogue (starts with sample rows)
scripts/config.py         all settings: keywords, subgroups, providers
scripts/fetch_papers.py   pulls papers from OpenAlex
scripts/summarize.py      writes summaries + tags (free LLM)
scripts/update_database.py the job that ties it together
.github/workflows/update.yml  the weekly schedule
requirements.txt          one dependency (requests)
```

A note on accuracy: summaries are machine-generated and should be checked
against the source before citing. Entries the system couldn't summarise are
marked `[check]` on the site.
