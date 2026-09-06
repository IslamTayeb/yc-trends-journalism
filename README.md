# yc-trends-journalism

How has the composition of Y Combinator batches changed from 2021 to the present, **according to YC's own taxonomy**?

Phase 1 (this repo state): a reproducible pipeline over YC's public directory metadata (industry, subindustry, tags, regions, status) plus YC's Requests for Startups. No LLM classification, no invented categories.

## Deliverables

| File | What |
|---|---|
| `report.md` | Generated narrative report (every number comes from the CSVs) |
| `yc_native_analysis.xlsx` | 17-tab workbook: Companies, Batch Summary, Industries, Industry Trends, Subindustries, Subindustry Trends, Tags, Tag Trends, Category Rankings, Tag Co-occurrence, Geography, Diversity, Taxonomy Changes, Data Quality, RFS, RFS Label Mentions |
| `figures/` | 62 PNG charts (batch size, industries, subindustries, tags, standalone native categories, concentration, diversity, geography, RFS) |
| `data/processed/` | All CSV tables (`yc_companies_native.csv`, `yc_company_tags.csv`, `yc_company_industries.csv`, `yc_company_subindustries.csv`, `yc_batch_summary.csv`, `yc_*_trends.csv`, `yc_*_trend_stats.csv`, `yc_tag_cooccurrence*.csv`, `yc_geography_*.csv`, `yc_diversity.csv`, `yc_taxonomy_history.csv`, `yc_relabel_events.csv`, `yc_rfs_*.csv`, ...) |
| `data/quality/` | Cross-checks against the source's own list files, 50-record spot check, data-quality report |
| `data/provenance.json` | Source commits, retrieval time, snapshot list |

## Sources

- **Primary:** [yc-oss/api](https://github.com/yc-oss/api) — daily dump of YC's public Algolia directory (6,203 companies, 2005-present). `companies/all.json` is committed under `data/raw/yc-oss-api/`; the git history of that repo (Aug 2024 onward) supplies monthly snapshots used to detect taxonomy changes.
- **Secondary (enrichment only):** [EXTREMOPHILARUM/yc-dataset](https://github.com/EXTREMOPHILARUM/yc-dataset).
- **RFS:** https://www.ycombinator.com/rfs (live) + Wayback Machine captures of the same URL (2014-2026) + `ycombinator.com/rfs1..10.html` essays (2009-2014). Raw HTML is kept locally (gitignored); parsed tables are committed.

Coverage caveat: the directory lists publicly launched companies with YC profiles, not every company ever accepted.

## Run

```bash
uv sync
scripts/fetch_sources.sh          # clone/copy sources, extract snapshots, download RFS pages
uv run python run_all.py          # everything else (~30 s)
```

Configuration lives in `config.yaml`; `START_YEAR`, `END_YEAR`, `MIN_FULL_BATCH`, `OUT_DIR`, `FIG_DIR` can also be set as environment variables:

```bash
START_YEAR=2016 OUT_DIR=out2016/processed FIG_DIR=out2016/figures uv run python run_all.py
```

## Method notes

- `share` = companies with the label / all companies in the batch. Batches under `MIN_FULL_BATCH` (50) companies are "in progress" and excluded from rankings and latest-share statistics.
- Batches where more than half the companies have zero tags (currently Winter 2026, Spring 2026) are excluded from tag statistics only.
- Emergence classes (Emerging / Declining / Spiky / Persistent) are rule-based; thresholds are in `config.yaml` and printed in the workbook README tab and `report.md`.
- The "RFS Label Mentions" table is an exact string match of YC label names in RFS text, not a semantic mapping.
- Nothing is merged: near-duplicate labels (`AI` / `Artificial Intelligence`, `Biotech` / `Biotechnology`, ...) are listed in the Taxonomy Changes tab but kept separate everywhere.

## Layout

```
config.yaml  run_all.py  scripts/fetch_sources.sh
src/ycnative/   config load batches taxonomy trends emergence rankings cooccurrence geography diversity
                taxonomy_history enrichment rfs_fetch rfs quality figures workbook report snapshots fetch
data/raw/       yc-oss-api/ (all.json, meta.json)  yc-dataset/  snapshots/ (gitignored blobs)  rfs/ (gitignored html)
data/processed/ data/quality/ figures/ report.md yc_native_analysis.xlsx
```
