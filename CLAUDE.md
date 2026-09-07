# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A journalism data project: how has the composition of Y Combinator batches changed over time? **Phase 1 (done)** uses only YC's native taxonomy (`industry`, `subindustry`, `tags`, `regions`, `status`) plus YC's Requests for Startups (RFS). Phase 2 (not started) will add semantic/LLM classification of company descriptions. Until then: **no LLM classification, no invented categories, no merging of YC labels, no causal language** in outputs.

## Commands

```bash
uv sync                                   # deps (pandas, matplotlib, openpyxl, bs4, lxml, pyyaml)
scripts/fetch_sources.sh                  # (re)download sources: clones, snapshots, RFS pages. Needs network.
uv run python run_all.py                  # full pipeline, ~30-40 s. Writes data/processed, data/quality, figures/, report.md, yc_native_analysis.xlsx
START_YEAR=2016 OUT_DIR=out16/processed FIG_DIR=out16/figures uv run python run_all.py   # any other window; root deliverables land in out16/ instead of repo root
```

There are no tests; `run_all.py` is the check. It fails loudly if the 50-record spot check against raw JSON mismatches, and prints `cross-check mismatches: N of 445` (must be 0: our per-batch/industry/tag counts vs the source's own list files). `data/all_years/processed/` is a committed `START_YEAR=2005` run kept for time-slice analyses.

Modules are importable only with `src` on the path (`run_all.py` inserts it; scripts use `PYTHONPATH=src uv run python -m ycnative.<module>`). The package is not installed editable despite `pyproject.toml`.

## Pipeline shape (`run_all.py` -> `src/ycnative/`)

One linear function builds a `ctx` dict that every later stage reads. Order matters:

1. `fetch.write_provenance` -> `load.read_all/to_frame/select_window` (raw fields kept verbatim; derived fields are prefixed `n_`) -> long tables (`yc_company_tags/industries/subindustries.csv`).
2. `batches.batch_summary` also decides two flags used everywhere downstream: `is_partial_batch` (< `MIN_FULL_BATCH`, in-progress batches) and `low_tag_coverage` (> `TAG_COVERAGE_MAX_ZERO_TAG_PCT` zero-tag companies). Partial batches are excluded from rankings/"latest"; low-coverage batches are excluded from **tag** statistics only.
3. `trends.matrices` + `trends.trend_stats` run generically three times (industry = top-level `industry`; subindustry = full `"Parent -> Child"` string; tag). `emergence.classify` (rule-based, thresholds in `config.yaml`) and `rankings` hang off that.
4. `cooccurrence`, `geography`, `diversity` (includes rarefied tag richness), then `taxonomy_history` (diffs the monthly `data/raw/snapshots/all_*.json` blobs), `enrichment` (secondary source, `ycds_*` columns, never overrides YC labels), `rfs` (parse + string-match label mentions + before/after shares), `quality`, `figures`, `workbook`, `report`.

`report.md` is **generated** by `report.py`; every number is read from a DataFrame. Edit the generator, not the markdown. The workbook (`workbook.py`) is 17 tabs; strings pass through `_san()` because company descriptions contain control characters that openpyxl rejects.

## Data facts that shape the code

- Batch names are `"Winter 2021"`, `"Spring 2025"`, etc.; code is W/X/S/F + yy (X = Spring, YC's own convention). One record has batch `"Unspecified"` (id 64, YC itself) and is excluded.
- `industries` array = [parent, child]; `subindustry` = `"Parent -> Child"` or bare parent. Cross-checks rely on this being exact.
- YC **retroactively relabels** companies constantly (measured in `yc_relabel_events.csv`); the dominant flow is `AI` <-> `Artificial Intelligence`. Never merge those two; report them as one measurement with two names. `Defense` (tag and subindustry) was introduced in 2026.
- Winter 2026 and Spring 2026 have ~75% zero-tag companies; pre-2011 batches also have low tag coverage.
- Git history of yc-oss/api only reaches back to 2024-08-22; `snapshots.py` picks earliest + first commit of each month.
- Wayback `id_` captures often arrive gzip-compressed; `rfs_fetch.get` gunzips on magic bytes. The live `/rfs` page renders only the current edition; earlier seasonal editions come from monthly Wayback captures. `rfs.py` walks the DOM in document order (h2 = edition, h3 = request, `By <partner>` span) and must not mutate the tree mid-walk.

## Repo hygiene

- Raw scraped HTML (`data/raw/rfs/**/*.html`), git clones, snapshot blobs, and the per-list JSON copies are gitignored; only `companies/all.json`, `meta.json`, `index.json` and parsed tables are committed. A committed YC page once tripped GitHub secret scanning (YC's public Maps key) and history had to be rewritten: keep it that way.
- Commit and push at working checkpoints; the user follows the GitHub repo.
- Deliverables go to the user's Mac via the `deliver-to-mac` skill (reverse tunnel on `127.0.0.1:2222`, see `/work/projects/AGENTS.md`).
