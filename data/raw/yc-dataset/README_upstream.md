# YC Startup Dataset

A comprehensive, agent-friendly dataset of every Y Combinator startup — scraped, merged, and structured as markdown files organized by batch.

## Data

**5,762 companies** across all YC batches (2005–2026), with 173 including post-mortem reports from dead/acquired startups.

```
data/
  index.json              # Lightweight lookup (slug, name, batch, status, has_postmortem)
  S05/
    reddit/
      company.md          # Core info (YAML frontmatter) + description
      founders.md         # Founder profiles with social links
      news.md             # Press coverage
      launches.md         # YC launch posts
    ...
  W15/
    20n/
      company.md
      founders.md
      postmortem.md       # Post-mortem report (startups.rip)
      buildplan.md        # Rebuild playbook
      techspecs.md        # Technical specs preview + TOC
    ...
```

Batch codes: `S05` = Summer 2005, `W07` = Winter 2007, `F24` = Fall 2024, `Sp25` = Spring 2025.

### Sources

| Source | What | Count |
|--------|------|-------|
| [YC Directory](https://www.ycombinator.com/companies) | Company profiles, industries, tags, hiring status | 5,758 |
| YC Detail Pages | Founders, social links, news, launches, descriptions | 5,758 |
| [Startups.RIP](https://startups.rip) | Post-mortem reports, build plans, technical specs | 173 |

### Raw Data

Raw JSON scraper output is preserved in `raw/` for programmatic access:
- `yc_directory.json` — Algolia API dump
- `yc_details.json` — Detail page extractions
- `startups_rip.json` — Post-mortem data

## Usage

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Scrape (outputs to raw/)
uv run python3 scraper.py --source yc          # YC directory
uv run python3 scraper.py --source yc-details   # YC detail pages (~30 min)
uv run python3 scraper.py --source rip           # startups.rip (~2 min)
uv run python3 scraper.py --source all           # Everything

# Transform raw JSON → markdown (raw/ → data/)
uv run python3 transform.py
```

## For Agents

Each company is a directory of small markdown files with YAML frontmatter — designed for LLM agents to read efficiently without loading large JSON blobs.

Use `data/index.json` to find companies by slug, batch, or status, then read individual files as needed.

### `/analyze` Skill

A Claude Code custom skill that generates comprehensive startup analysis for any company in the dataset — the same framework used by startups.rip but applicable to any startup (active, dead, or acquired).

```bash
/analyze reddit           # Full analysis (report + build plan + tech specs)
/analyze reddit report    # Just the research report
```

Generates three files per company:
- **Research Report** (`postmortem.md`) — founding story, timeline, product analysis, market position, business model, traction, post-mortem/current status, key lessons. Citation-heavy, 8+ sources.
- **Build Plan** (`buildplan.md`) — how to rebuild the company today. Market analysis, competition map, MVP features, go-to-market strategy with specific pricing.
- **Technical Specs** (`techspecs.md`) — full system architecture: tech stack, database schema, API routes, user flows, auth, deployment.

The skill includes detailed per-section guides and real examples (20n) as quality anchors. See `.claude/skills/analyze/`.
