# Full-stack AI companies

A separate pass, outside the Phase 1 pipeline: every YC company from Winter 2019 on is read once against Jared Friedman's
definition of a full-stack AI company (YC Requests for Startups, Summer 2025) and given one of seven categories. Phase 1
uses only YC's own labels; this directory is the one place where a category is assigned by reading descriptions, so it
stays out of `data/processed`, `report.md` and the dashboard.

```bash
uv run python fullstack/prepare_chunks.py      # work/chunks/chunk_NN.jsonl from data/all_years/processed (gitignored, regenerable)
# classify: each chunk is read by a Claude agent against rubric.md and written to work/labels/chunk_NN.jsonl (committed)
uv run python fullstack/collect.py             # validates every id is labelled once, applies review_overrides.csv -> data/yc_fullstack_labels.csv, data/yc_fullstack_by_batch.csv
uv run python fullstack/make_figure.py         # figures/yc_fullstack_ai.svg, yc_fullstack_industry.svg (+ PNG light/dark, PDF, preview.html), same styling as blog/
uv run python fullstack/make_figure.py --bare  # figures/bare/: plot-only versions with inlined styles + transparent PNG, for Word / Docs
```

## Files

| path | what |
|---|---|
| `rubric.md` | the definition (quoted verbatim), the seven categories, the tie-break rules, the output format; the classifier gets nothing else |
| `work/labels/chunk_NN.jsonl` | raw first-pass classifier output, one JSON line per company: id, category, confidence, reason |
| `review_overrides.csv` | second pass: every first-pass `full_stack_ai` was re-read by one reviewer; the 55 that did not hold are moved here with a note |
| `data/yc_fullstack_labels.csv` | one row per company with YC's fields, the category, a plain-English `caption`, confidence and the reason |
| `data/yc_fullstack_by_batch.csv` | per batch: count per category, share of batch, share among AI companies, high-confidence count |
| `data/yc_fullstack_by_industry.csv` | per YC top-level industry: count and share among full-stack AI companies vs among all companies, Winter 2023 to Summer 2026, and the ratio |
| `figures/yc_fullstack_ai.svg` | Fig 4: share of batch that is full-stack AI, with rules at ChatGPT (Nov 2022) and the RFS (Jun 2025) |
| `figures/yc_fullstack_industry.svg` | Fig 5: dumbbell per YC industry, share among full-stack AI companies (blue) vs among all companies (gray), post-ChatGPT full batches |
| `figures/*_light.png`, `*_dark.png`, `*.pdf`, `preview.html`, `bare/` | rasters, vector PDFs, side-by-side preview with theme toggle, and plot-only versions, as in `blog/figures` |

## Categories

`full_stack_ai` (runs the service itself, AI does the work), `sells_ai_to_industry` (the "build an agent and sell it to
law firms" case), `ai_infra`, `ai_other`, `full_stack_non_ai` (tech-enabled operator, AI not at the core), `not_ai`,
`unclear`. `caption` in the labels CSV spells these out.

## Caveats

- Classification is a reading of YC's *current* description text (2026-09-06 snapshot). Companies rewrite their copy
  after pivots, and YC retags, so early batches are judged on what the company says today.
- First pass: one reader per chunk of 150 companies (16 agents). Their bar for `full_stack_ai` differed (one counted AI
  receptionists sold to clinics, another did not), so every first-pass positive (234) was re-read by a single reviewer
  against the rubric; 55 were moved, leaving 179. The other six categories were not re-read, so `full_stack_non_ai`
  in particular is inconsistent between chunks (one reader counted every payments company, the next none) and is kept
  in the CSV but not plotted. Negatives were only screened by keyword for missed "AI-native X firm" phrasing.
- `category_first_pass` and `reviewed` in the labels CSV show what changed. `confidence` is the reader's own; treat
  `low` as a coin flip. Spot-check before quoting a company by name: the `reason` column quotes the deciding phrase.
- Where the second reviewer drew the line: a company counts when it delivers a service that customers would otherwise
  buy from a firm (tax prep, bookkeeping, law, brokerage, lending, collections, recruiting agency, marketing agency,
  clinic, BPO) and says AI or agents do the work. "AI employee" products sold into a company's own staff functions
  (AI receptionist, AI SDR, browser automation), consumer apps, robots sold as products, AI drug-discovery biotechs and
  marketplaces do not.
- Winter 2019 to Summer 2026 only, matching the blog figures; Fall 2026 (35 companies) is in the CSVs but not the figure.
- The classifier was Claude (Sonnet) reading 150 companies at a time, chunked in batch order. Chunk boundaries are
  recorded in the `chunk` column of the labels CSV.
