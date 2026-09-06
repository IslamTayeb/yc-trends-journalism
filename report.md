# What kinds of companies is YC funding, 2021-present, according to YC's own taxonomy

Scope of this phase: YC's native labels only (`industry`, `subindustry`, `tags`, `regions`, `status`), plus YC's own Requests for Startups (RFS) text. No LLM classification, no custom buckets, no causal claims. Every number below is produced by `run_all.py` from `data/processed/*.csv`.

## 1. Data and provenance

- Primary source: [https://github.com/yc-oss/api](https://github.com/yc-oss/api) at commit `a87f0584d5617fbd5996c9e4db6244bab15b0dc5` (2026-09-06); source `meta.json` last_updated 2026-09-06T02:01:23Z; retrieved 2026-09-06T22:05:07Z. Directory size: 6203 companies.
- Selected: **3729 companies in 18 batches** (Winter 2021 to Winter 2027); 2474 companies outside the window (or with batch 'Unspecified') excluded.
- Coverage caveat: the directory lists publicly launched companies with a YC profile, not every company ever accepted.
- Secondary source (enrichment only): https://github.com/EXTREMOPHILARUM/yc-dataset at `03784c3f43` (2026-03-11); covers 87.69% of selected companies. It is a different-dated dump of the same Algolia index; industry agrees for 97.68% of shared companies, tags for 75.78% (see section 9).
- Historical snapshots of `companies/all.json` from the primary repo's git history: 24 monthly snapshots, 2024-08-22 to 2026-09-01.
- Data quality: 0 duplicate ids; source cross-check 0 mismatches in 445 comparisons (per-batch, per-industry, per-tag counts vs the source's own list files); random spot check of 50 companies x 24 fields: 0 mismatches. Full report: `data/quality/`.

**Conventions.** share = companies carrying the label / all companies in the batch. Batches with fewer than 50 companies (Fall 2026, Winter 2027) are in progress and excluded from rankings and 'latest' figures. '2021' shares pool all 2021 batches. 'Latest' = Summer 2026.

**Tag-coverage warning.** In Winter 2026, Spring 2026 most companies have no tags at all (Winter 2026: 75.9% zero-tag, Spring 2026: 74.4% zero-tag), versus 1.3% in Summer 2026. Tag shares for those batches are shown in the matrices but excluded from all tag statistics; 'latest' for tags = Summer 2026. Industry and subindustry fields are populated for every company, so they are unaffected.

## 2. Batch sizes

| batch | companies | active | acquired | inactive | hiring | median team | % missing team size | zero-tag | partial |
|---|---|---|---|---|---|---|---|---|---|
| Winter 2021 | 336 | 230 | 42 | 64 | 79 | 12.0 | 0.6 | 8 | False |
| Summer 2021 | 391 | 289 | 38 | 64 | 87 | 10.0 | 2.3 | 9 | False |
| Winter 2022 | 398 | 313 | 37 | 48 | 84 | 10.0 | 1.5 | 9 | False |
| Summer 2022 | 234 | 187 | 13 | 34 | 65 | 7.0 | 0.8 | 10 | False |
| Winter 2023 | 274 | 202 | 34 | 38 | 81 | 5.0 | 2.2 | 35 | False |
| Summer 2023 | 220 | 180 | 18 | 22 | 90 | 5.0 | 0.9 | 33 | False |
| Winter 2024 | 248 | 213 | 12 | 23 | 91 | 5.0 | 2.8 | 43 | False |
| Summer 2024 | 248 | 234 | 6 | 8 | 102 | 4.0 | 2.0 | 46 | False |
| Fall 2024 | 94 | 90 | 1 | 3 | 39 | 3.0 | 0.0 | 20 | False |
| Winter 2025 | 166 | 161 | 3 | 2 | 66 | 4.0 | 1.2 | 38 | False |
| Spring 2025 | 143 | 137 | 3 | 3 | 57 | 3.0 | 2.1 | 33 | False |
| Summer 2025 | 166 | 162 | 3 | 1 | 71 | 4.0 | 4.2 | 49 | False |
| Fall 2025 | 146 | 142 | 1 | 3 | 61 | 3.0 | 2.7 | 28 | False |
| Winter 2026 | 199 | 196 | 0 | 3 | 60 | 2.0 | 1.5 | 151 | False |
| Spring 2026 | 195 | 195 | 0 | 0 | 59 | 3.0 | 1.0 | 145 | False |
| Summer 2026 | 235 | 235 | 0 | 0 | 14 | 2.0 | 1.3 | 3 | False |
| Fall 2026 | 35 | 35 | 0 | 0 | 6 | 2.0 | 0.0 | 1 | True |
| Winter 2027 | 1 | 1 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | True |

Listed batch size peaked at 398 (Winter 2022) and was smallest at 94 (Fall 2024); YC moved from two to four batches a year starting Fall 2024. Status fields age with the batch (recent batches are almost entirely 'Active'), so status is not comparable across batches.

## 3. YC's taxonomy as present in the data

- 8 top-level industries, 58 subindustry strings (50 distinct child labels), 303 distinct tags, 84 distinct region strings.
- Every company has an `industry` and a `subindustry`; 1108 companies carry only the parent (e.g. subindustry = 'B2B'). 661 companies have zero tags (17.7%), 2859 have more than one tag; 2621 have two entries in `industries` (parent + child; there are never more than two).
- 161 companies lack a long description, 63 lack team size, 86 lack a location string.
- Full inventories: `yc_industries.csv`, `yc_subindustries.csv`, `yc_tags.csv` (workbook tabs Industries / Subindustries / Tags).

## 4. Industries (YC top-level `industry`)

| industry | share 2021 | share Summer 2026 | pp change | rank 2021 | rank latest | peak batch | peak share | class |
|---|---|---|---|---|---|---|---|---|
| B2B | 47.2 | 51.9 | 4.7 | 1 | 1 | Summer 2023 | 69.1 | Persistent |
| Industrials | 5.9 | 23.8 | 17.9 | 5 | 2 | Summer 2026 | 23.8 | Emerging |
| Healthcare | 14.4 | 8.9 | -5.5 | 3 | 3 | Summer 2021 | 16.4 | Persistent |
| Fintech | 15.7 | 6.8 | -8.9 | 2 | 4 | Winter 2022 | 22.6 | Spiky |
| Consumer | 10.7 | 4.7 | -6.0 | 4 | 5 | Fall 2024 | 11.7 | Persistent |
| Real Estate and Construction | 1.9 | 2.6 | 0.6 | 7 | 6 | Fall 2024 | 4.3 | Low-volume / mixed |
| Government | 0.3 | 0.9 | 0.6 | 8 | 7 | Winter 2025 | 2.4 | Spiky |
| Education | 3.9 | 0.4 | -3.4 | 6 | 8 | Winter 2021 | 3.9 | Declining |

- **B2B**: 47.2% of the 2021 batches to 51.9% of Summer 2026 (+4.7 pp); rank 1 to 1; peak 69.1% in Summer 2023.
- **Industrials**: 5.9% of the 2021 batches to 23.8% of Summer 2026 (+17.9 pp); rank 5 to 2; peak 23.8% in Summer 2026.
- **Healthcare**: 14.4% of the 2021 batches to 8.9% of Summer 2026 (-5.5 pp); rank 3 to 3; peak 16.4% in Summer 2021.
- **Fintech**: 15.7% of the 2021 batches to 6.8% of Summer 2026 (-8.9 pp); rank 2 to 4; peak 22.6% in Winter 2022.
- **Consumer**: 10.7% of the 2021 batches to 4.7% of Summer 2026 (-6.0 pp); rank 4 to 5; peak 11.7% in Fall 2024.
- **Real Estate and Construction**: 1.9% of the 2021 batches to 2.6% of Summer 2026 (+0.6 pp); rank 7 to 6; peak 4.3% in Fall 2024.
- **Government**: 0.3% of the 2021 batches to 0.9% of Summer 2026 (+0.6 pp); rank 8 to 7; peak 2.4% in Winter 2025.
- **Education**: 3.9% of the 2021 batches to 0.4% of Summer 2026 (-3.4 pp); rank 6 to 8; peak 3.9% in Winter 2021.

Figures: `figures/largest_industries_share.png`, `figures/fastest_moving_industry.png`, one file per industry `figures/industry_*.png`.

## 5. Subindustries (YC `subindustry`, 'Parent -> Child')

Largest gains (pp of batch):

| subindustry | 2021 | Summer 2026 | pp | rank 2021 | rank latest | peak | peak share | class |
|---|---|---|---|---|---|---|---|---|
| Industrials -> Manufacturing and Robotics | 1.0 | 10.2 | 9.2 | 36 | 3 | Summer 2026 | 10.2 | Emerging |
| B2B | 8.7 | 17.4 | 8.8 | 1 | 1 | Winter 2026 | 23.1 | Emerging |
| B2B -> Infrastructure | 2.9 | 10.6 | 7.7 | 10 | 2 | Winter 2026 | 11.6 | Emerging |
| Industrials | 0.1 | 6.0 | 5.8 | 51 | 4 | Summer 2026 | 6.0 | Emerging |
| Industrials -> Defense | 0.1 | 3.8 | 3.7 | 51 | 7 | Summer 2026 | 3.8 | Emerging |
| Healthcare | 1.9 | 5.1 | 3.2 | 20 | 6 | Fall 2024 | 6.4 | Low-volume / mixed |
| B2B -> Security | 1.8 | 3.0 | 1.2 | 22 | 9 | Spring 2025 | 5.6 | Low-volume / mixed |
| Fintech -> Insurance | 1.0 | 2.1 | 1.2 | 36 | 14 | Spring 2026 | 2.6 | Low-volume / mixed |
| B2B -> Supply Chain and Logistics | 2.6 | 3.4 | 0.8 | 13 | 8 | Summer 2025 | 3.6 | Low-volume / mixed |
| Government | 0.3 | 0.9 | 0.6 | 48 | 23 | Winter 2025 | 2.4 | Spiky |

Largest declines (pp of batch):

| subindustry | 2021 | Summer 2026 | pp | rank 2021 | rank latest | peak | peak share | class |
|---|---|---|---|---|---|---|---|---|
| Fintech -> Payments | 3.4 | 0.0 | -3.4 | 6 | 41 | Winter 2022 | 4.0 | Declining |
| Education | 3.9 | 0.4 | -3.4 | 3 | 30 | Winter 2021 | 3.9 | Declining |
| Consumer -> Food and Beverage | 2.6 | 0.0 | -2.6 | 13 | 41 | Winter 2021 | 2.7 | Declining |
| B2B -> Human Resources | 2.5 | 0.0 | -2.5 | 15 | 41 | Summer 2021 | 3.6 | Declining |
| Fintech -> Credit and Lending | 2.5 | 0.0 | -2.5 | 15 | 41 | Winter 2021 | 3.3 | Declining |
| Healthcare -> Consumer Health and Wellness | 3.3 | 0.9 | -2.5 | 8 | 23 | Summer 2021 | 4.1 | Declining |
| B2B -> Engineering, Product and Design | 8.4 | 6.0 | -2.4 | 2 | 4 | Fall 2024 | 17.0 | Persistent |
| B2B -> Marketing | 2.8 | 0.4 | -2.3 | 12 | 30 | Fall 2025 | 4.8 | Low-volume / mixed |
| Healthcare -> Healthcare IT | 2.2 | 0.4 | -1.8 | 18 | 30 | Summer 2023 | 4.1 | Low-volume / mixed |
| Fintech -> Consumer Finance | 2.1 | 0.4 | -1.6 | 19 | 30 | Winter 2021 | 2.1 | Low-volume / mixed |

Standalone native categories (each kept separate; `figures/subindustry_*.png`):

- **Industrials -> Manufacturing and Robotics**: first observed Winter 2021; 1.0% in 2021 to 10.2% in Summer 2026 (+9.2 pp); peak 10.2% (24 companies) in Summer 2026; class: Emerging.
- **Industrials -> Defense**: first observed Winter 2021; 0.1% in 2021 to 3.8% in Summer 2026 (+3.7 pp); peak 3.8% (9 companies) in Summer 2026; class: Emerging.
- **Industrials -> Aviation and Space**: first observed Winter 2021; 1.5% in 2021 to 1.3% in Summer 2026 (-0.2 pp); peak 3.2% (3 companies) in Fall 2024; class: Low-volume / mixed.
- **Industrials -> Drones**: first observed Summer 2021; 0.3% in 2021 to 0.0% in Summer 2026 (-0.3 pp); peak 1.0% (2 companies) in Winter 2026; class: Low-volume / mixed.
- **Industrials -> Energy**: first observed Winter 2021; 1.1% in 2021 to 1.3% in Summer 2026 (+0.2 pp); peak 3.0% (6 companies) in Winter 2026; class: Spiky.
- **Healthcare -> Industrial Bio**: first observed Winter 2021; 0.4% in 2021 to 0.0% in Summer 2026 (-0.4 pp); peak 0.8% (2 companies) in Summer 2024; class: Low-volume / mixed.
- **Healthcare -> Medical Devices**: first observed Winter 2021; 1.5% in 2021 to 0.0% in Summer 2026 (-1.5 pp); peak 2.0% (8 companies) in Summer 2021; class: Spiky.
- **Real Estate and Construction -> Construction**: first observed Winter 2021; 0.8% in 2021 to 1.3% in Summer 2026 (+0.5 pp); peak 3.2% (3 companies) in Fall 2024; class: Spiky.
- Real Estate and Construction: not present as a YC subindustry in the selected data.
- **Industrials -> Agriculture**: first observed Summer 2021; 0.3% in 2021 to 0.4% in Summer 2026 (+0.2 pp); peak 1.2% (2 companies) in Winter 2025; class: Low-volume / mixed.
- **Industrials -> Climate**: first observed Winter 2021; 1.1% in 2021 to 0.9% in Summer 2026 (-0.2 pp); peak 2.5% (10 companies) in Winter 2022; class: Spiky.
- **Industrials -> Automotive**: first observed Winter 2021; 0.4% in 2021 to 0.0% in Summer 2026 (-0.4 pp); peak 1.1% (1 companies) in Fall 2024; class: Low-volume / mixed.
- **Healthcare -> Healthcare IT**: first observed Winter 2021; 2.2% in 2021 to 0.4% in Summer 2026 (-1.8 pp); peak 4.1% (9 companies) in Summer 2023; class: Low-volume / mixed.
- **Healthcare -> Drug Discovery and Delivery**: first observed Summer 2021; 1.2% in 2021 to 1.3% in Summer 2026 (+0.0 pp); peak 2.6% (7 companies) in Winter 2023; class: Spiky.
- **B2B -> Supply Chain and Logistics**: first observed Winter 2021; 2.6% in 2021 to 3.4% in Summer 2026 (+0.8 pp); peak 3.6% (6 companies) in Summer 2025; class: Low-volume / mixed.
- **B2B -> Finance and Accounting**: first observed Winter 2021; 3.9% in 2021 to 2.6% in Summer 2026 (-1.3 pp); peak 4.7% (13 companies) in Winter 2023; class: Declining.
- Semiconductors: not present as a YC subindustry in the selected data.

Note the parent-only strings ('B2B', 'Industrials', 'Healthcare' with no child) are themselves among the biggest movers: companies are increasingly filed under the parent without a child label (see section 9).

## 6. Tags (YC `tags`)

Top 20 tags in Summer 2026 by share of batch:

| tag | 2021 | Summer 2026 | pp | rank 2021 | rank latest | peak | peak share | class |
|---|---|---|---|---|---|---|---|---|
| Artificial Intelligence | 12.0 | 37.0 | 25.1 | 4 | 1 | Winter 2024 | 37.5 | Emerging |
| AI | 9.1 | 31.5 | 22.4 | 6 | 2 | Fall 2024 | 36.2 | Emerging |
| B2B | 24.8 | 22.6 | -2.2 | 2 | 3 | Summer 2022 | 38.0 | Persistent |
| Robotics | 1.7 | 11.9 | 10.3 | 35 | 4 | Summer 2026 | 11.9 | Emerging |
| Hard Tech | 2.8 | 10.6 | 7.9 | 19 | 5 | Summer 2026 | 10.6 | Emerging |
| SaaS | 29.4 | 10.2 | -19.2 | 1 | 6 | Winter 2023 | 31.4 | Declining |
| Developer Tools | 9.2 | 9.8 | 0.6 | 5 | 7 | Fall 2024 | 19.1 | Persistent |
| Hardware | 1.7 | 8.5 | 6.9 | 35 | 8 | Summer 2026 | 8.5 | Emerging |
| Infrastructure | 1.4 | 8.1 | 6.7 | 42 | 9 | Summer 2026 | 8.1 | Emerging |
| Manufacturing | 0.8 | 6.8 | 6.0 | 65 | 10 | Summer 2026 | 6.8 | Emerging |
| Enterprise Software | 1.1 | 6.0 | 4.9 | 51 | 11 | Summer 2026 | 6.0 | Emerging |
| Fintech | 19.1 | 6.0 | -13.2 | 3 | 11 | Winter 2022 | 23.1 | Declining |
| Reinforcement Learning | 0.0 | 6.0 | 6.0 | 231 | 11 | Summer 2026 | 6.0 | Emerging |
| Machine Learning | 4.1 | 5.1 | 1.0 | 12 | 14 | Fall 2024 | 6.4 | Persistent |
| Workflow Automation | 0.7 | 4.7 | 4.0 | 75 | 15 | Summer 2026 | 4.7 | Emerging |
| Finance | 1.1 | 4.7 | 3.6 | 51 | 15 | Summer 2026 | 4.7 | Emerging |
| Automation | 0.7 | 4.7 | 4.0 | 75 | 15 | Summer 2026 | 4.7 | Emerging |
| Healthcare | 3.4 | 4.7 | 1.2 | 14 | 15 | Summer 2023 | 9.1 | Low-volume / mixed |
| Generative AI | 2.6 | 4.3 | 1.6 | 23 | 19 | Winter 2023 | 17.9 | Emerging |
| Biotech | 2.8 | 3.8 | 1.1 | 19 | 20 | Summer 2024 | 4.4 | Low-volume / mixed |

Fastest-growing tags (pp):

| tag | 2021 | Summer 2026 | pp | first batch | class |
|---|---|---|---|---|---|
| Artificial Intelligence | 12.0 | 37.0 | 25.1 | Winter 2021 | Emerging |
| AI | 9.1 | 31.5 | 22.4 | Winter 2021 | Emerging |
| Robotics | 1.7 | 11.9 | 10.3 | Winter 2021 | Emerging |
| Hard Tech | 2.8 | 10.6 | 7.9 | Winter 2021 | Emerging |
| Hardware | 1.7 | 8.5 | 6.9 | Winter 2021 | Emerging |
| Infrastructure | 1.4 | 8.1 | 6.7 | Winter 2021 | Emerging |
| Manufacturing | 0.8 | 6.8 | 6.0 | Winter 2021 | Emerging |
| Reinforcement Learning | 0.0 | 6.0 | 6.0 | Winter 2023 | Emerging |
| Enterprise Software | 1.1 | 6.0 | 4.9 | Winter 2021 | Emerging |
| Workflow Automation | 0.7 | 4.7 | 4.0 | Winter 2021 | Emerging |
| Automation | 0.7 | 4.7 | 4.0 | Winter 2021 | Emerging |
| Industrial | 0.1 | 3.8 | 3.7 | Summer 2021 | Emerging |
| Finance | 1.1 | 4.7 | 3.6 | Winter 2021 | Emerging |
| Semiconductors | 0.0 | 3.0 | 3.0 | Summer 2023 | Spiky |
| Energy | 1.0 | 3.8 | 2.9 | Winter 2021 | Spiky |

Fastest-declining tags (pp):

| tag | 2021 | Summer 2026 | pp | peak | peak share | class |
|---|---|---|---|---|---|---|
| SaaS | 29.4 | 10.2 | -19.2 | Winter 2023 | 31.4 | Declining |
| Fintech | 19.1 | 6.0 | -13.2 | Winter 2022 | 23.1 | Declining |
| E-commerce | 6.1 | 0.9 | -5.2 | Summer 2021 | 6.4 | Declining |
| Marketplace | 7.3 | 2.6 | -4.7 | Summer 2021 | 8.4 | Declining |
| Climate | 4.4 | 0.4 | -4.0 | Winter 2022 | 5.0 | Declining |
| Consumer Health Services | 4.7 | 0.9 | -3.8 | Summer 2021 | 5.4 | Declining |
| Education | 4.4 | 0.9 | -3.6 | Summer 2021 | 4.6 | Declining |
| Payments | 3.2 | 0.0 | -3.2 | Summer 2022 | 6.4 | Declining |
| Community | 2.6 | 0.0 | -2.6 | Summer 2021 | 3.1 | Declining |
| eLearning | 2.8 | 0.4 | -2.3 | Winter 2021 | 3.6 | Declining |
| B2B | 24.8 | 22.6 | -2.2 | Summer 2022 | 38.0 | Persistent |
| Proptech | 2.1 | 0.0 | -2.1 | Winter 2022 | 3.5 | Low-volume / mixed |
| Digital Health | 2.9 | 0.9 | -2.0 | Winter 2022 | 3.5 | Low-volume / mixed |
| Subscriptions | 1.8 | 0.0 | -1.8 | Winter 2021 | 2.7 | Spiky |
| Delivery | 1.7 | 0.0 | -1.7 | Summer 2021 | 2.0 | Spiky |

Tags first observed after Winter 2021 (>= 5 companies overall): Reinforcement Learning (Winter 2023, 41), Industrial (Summer 2021, 31), DevOps (Summer 2021, 30), Data Science (Summer 2021, 24), Synthetic Biology (Summer 2021, 23), Advertising (Summer 2021, 23), Big Data (Summer 2021, 21), Semiconductors (Summer 2023, 19), Data Labeling (Summer 2021, 18), ML (Summer 2021, 18), Search (Summer 2021, 18), Drones (Summer 2021, 18), Regtech (Summer 2021, 17), Automotive (Winter 2022, 16), Transportation (Summer 2021, 15), Solar Power (Summer 2021, 13), Payroll (Summer 2021, 11), Biotechnology (Summer 2021, 11), CRM (Summer 2021, 11), Electronics (Winter 2022, 10).

Tags that peaked and then declined (peak in a full batch before the last two, latest <= half of peak): SaaS (peak 31.4% in Winter 2023, now 10.2%), Fintech (peak 23.1% in Winter 2022, now 6.0%), Generative AI (peak 17.9% in Winter 2023, now 4.3%), Consumer (peak 9.8% in Winter 2022, now 2.6%), Marketplace (peak 8.4% in Summer 2021, now 2.6%), AI Assistant (peak 8.1% in Winter 2024, now 2.1%), Open Source (peak 7.7% in Winter 2023, now 3.4%), Payments (peak 6.4% in Summer 2022, now 0.0%), E-commerce (peak 6.4% in Summer 2021, now 0.9%), API (peak 6.0% in Summer 2022, now 1.3%), Productivity (peak 6.0% in Summer 2022, now 1.3%), Crypto / Web3 (peak 5.6% in Summer 2022, now 1.3%), Sales (peak 5.6% in Summer 2022, now 1.7%), Enterprise (peak 5.5% in Winter 2023, now 2.6%), Analytics (peak 5.5% in Winter 2023, now 1.3%).

Standalone tags (`figures/tag_*.png`):

- **Robotics**: first observed Winter 2021; 1.7% in 2021 to 11.9% in Summer 2026 (+10.3 pp); peak 11.9% (28) in Summer 2026; class: Emerging.
- **Hard Tech**: first observed Winter 2021; 2.8% in 2021 to 10.6% in Summer 2026 (+7.9 pp); peak 10.6% (25) in Summer 2026; class: Emerging.
- **Semiconductors**: first observed Summer 2023; 0.0% in 2021 to 3.0% in Summer 2026 (+3.0 pp); peak 3.0% (7) in Summer 2026; class: Spiky.
- **Defense**: first observed Winter 2021; 0.6% in 2021 to 3.4% in Summer 2026 (+2.9 pp); peak 3.4% (8) in Summer 2026; class: Emerging.
- **Aerospace**: first observed Winter 2021; 0.7% in 2021 to 2.1% in Summer 2026 (+1.4 pp); peak 3.2% (3) in Fall 2024; class: Spiky.
- **Drones**: first observed Summer 2021; 0.3% in 2021 to 2.1% in Summer 2026 (+1.9 pp); peak 2.1% (5) in Summer 2026; class: Spiky.
- **Manufacturing**: first observed Winter 2021; 0.8% in 2021 to 6.8% in Summer 2026 (+6.0 pp); peak 6.8% (16) in Summer 2026; class: Emerging.
- **Energy**: first observed Winter 2021; 1.0% in 2021 to 3.8% in Summer 2026 (+2.9 pp); peak 3.8% (9) in Summer 2026; class: Spiky.
- **Agriculture**: first observed Winter 2021; 0.3% in 2021 to 0.9% in Summer 2026 (+0.6 pp); peak 1.2% (2) in Summer 2025; class: Low-volume / mixed.
- **Construction**: first observed Winter 2021; 1.2% in 2021 to 3.4% in Summer 2026 (+2.2 pp); peak 3.4% (8) in Summer 2026; class: Low-volume / mixed.
- **Medical Devices**: first observed Winter 2021; 1.9% in 2021 to 0.4% in Summer 2026 (-1.5 pp); peak 3.1% (12) in Summer 2021; class: Spiky.
- **Healthcare**: first observed Winter 2021; 3.4% in 2021 to 4.7% in Summer 2026 (+1.2 pp); peak 9.1% (20) in Summer 2023; class: Low-volume / mixed.
- **Fintech**: first observed Winter 2021; 19.1% in 2021 to 6.0% in Summer 2026 (-13.2 pp); peak 23.1% (92) in Winter 2022; class: Declining.
- **Consumer**: first observed Winter 2021; 3.6% in 2021 to 2.6% in Summer 2026 (-1.0 pp); peak 9.8% (39) in Winter 2022; class: Low-volume / mixed.
- **Developer Tools**: first observed Winter 2021; 9.2% in 2021 to 9.8% in Summer 2026 (+0.6 pp); peak 19.1% (18) in Fall 2024; class: Persistent.
- **Artificial Intelligence**: first observed Winter 2021; 12.0% in 2021 to 37.0% in Summer 2026 (+25.1 pp); peak 37.5% (93) in Winter 2024; class: Emerging.
- **AI**: first observed Winter 2021; 9.1% in 2021 to 31.5% in Summer 2026 (+22.4 pp); peak 36.2% (34) in Fall 2024; class: Emerging.
- **Generative AI**: first observed Winter 2021; 2.6% in 2021 to 4.3% in Summer 2026 (+1.6 pp); peak 17.9% (49) in Winter 2023; class: Emerging.
- **Machine Learning**: first observed Winter 2021; 4.1% in 2021 to 5.1% in Summer 2026 (+1.0 pp); peak 6.4% (6) in Fall 2024; class: Persistent.
- **Crypto / Web3**: first observed Winter 2021; 2.2% in 2021 to 1.3% in Summer 2026 (-0.9 pp); peak 5.6% (13) in Summer 2022; class: Spiky.
- **Climate**: first observed Winter 2021; 4.4% in 2021 to 0.4% in Summer 2026 (-4.0 pp); peak 5.0% (20) in Winter 2022; class: Declining.
- **SaaS**: first observed Winter 2021; 29.4% in 2021 to 10.2% in Summer 2026 (-19.2 pp); peak 31.4% (86) in Winter 2023; class: Declining.
- **Marketplace**: first observed Winter 2021; 7.3% in 2021 to 2.6% in Summer 2026 (-4.7 pp); peak 8.4% (33) in Summer 2021; class: Declining.
- **Biotech**: first observed Winter 2021; 2.8% in 2021 to 3.8% in Summer 2026 (+1.1 pp); peak 4.4% (11) in Summer 2024; class: Low-volume / mixed.
- Space: not present as a YC tag in the selected data.

The derived charts `figures/derived_union_*.png` show the share of companies carrying ANY of a listed set of YC labels; they are explicitly labelled as derived aggregations and are not used in any statistic above.

## 7. Category rankings over time

Industries (rank by share, all batches):

| industry | rank 2021 | rank latest | change | share 2021 | share latest | pp | major mover |
|---|---|---|---|---|---|---|---|
| B2B | 1 | 1 | 0 | 47.2 | 51.9 | 4.7 | True |
| Industrials | 5 | 2 | 3 | 5.9 | 23.8 | 17.9 | True |
| Healthcare | 3 | 3 | 0 | 14.4 | 8.9 | -5.5 | True |
| Fintech | 2 | 4 | -2 | 15.7 | 6.8 | -8.9 | True |
| Consumer | 4 | 5 | -1 | 10.7 | 4.7 | -6.0 | True |
| Real Estate and Construction | 7 | 6 | 1 | 1.9 | 2.6 | 0.6 | False |
| Government | 8 | 7 | 1 | 0.3 | 0.9 | 0.6 | False |
| Education | 6 | 8 | -2 | 3.9 | 0.4 | -3.4 | True |

Tags flagged as major movers (|rank change| >= 5 or |pp| >= 3.0; full table in `yc_tag_rankings.csv`):

| tag | rank 2021 | rank latest | change | share 2021 | share latest | pp |
|---|---|---|---|---|---|---|
| Artificial Intelligence | 4 | 1 | 3 | 12.0 | 37.0 | 25.1 |
| AI | 6 | 2 | 4 | 9.1 | 31.5 | 22.4 |
| Robotics | 35 | 4 | 31 | 1.7 | 11.9 | 10.3 |
| Hard Tech | 19 | 5 | 14 | 2.8 | 10.6 | 7.9 |
| Hardware | 35 | 8 | 27 | 1.7 | 8.5 | 6.9 |
| Infrastructure | 42 | 9 | 33 | 1.4 | 8.1 | 6.7 |
| Manufacturing | 65 | 10 | 55 | 0.8 | 6.8 | 6.0 |
| Reinforcement Learning | 231 | 11 | 220 | 0.0 | 6.0 | 6.0 |
| Enterprise Software | 51 | 11 | 40 | 1.1 | 6.0 | 4.9 |
| Automation | 75 | 15 | 60 | 0.7 | 4.7 | 4.0 |
| Workflow Automation | 75 | 15 | 60 | 0.7 | 4.7 | 4.0 |
| Industrial | 185 | 20 | 165 | 0.1 | 3.8 | 3.7 |
| Finance | 51 | 15 | 36 | 1.1 | 4.7 | 3.6 |
| Semiconductors | 231 | 29 | 202 | 0.0 | 3.0 | 3.0 |
| Energy | 58 | 20 | 38 | 1.0 | 3.8 | 2.9 |
| Defense | 97 | 23 | 74 | 0.6 | 3.4 | 2.9 |
| Investing | 65 | 23 | 42 | 0.8 | 3.4 | 2.6 |
| Construction | 46 | 23 | 23 | 1.2 | 3.4 | 2.2 |
| Supply Chain | 42 | 23 | 19 | 1.4 | 3.4 | 2.0 |
| Cybersecurity | 97 | 31 | 66 | 0.6 | 2.6 | 2.0 |
| AIOps | 75 | 31 | 44 | 0.7 | 2.6 | 1.9 |
| Drones | 143 | 38 | 105 | 0.3 | 2.1 | 1.9 |
| Data Labeling | 185 | 43 | 142 | 0.1 | 1.7 | 1.6 |
| Enterprise | 51 | 31 | 20 | 1.1 | 2.6 | 1.5 |
| Insurance | 51 | 31 | 20 | 1.1 | 2.6 | 1.5 |
| Aerospace | 75 | 38 | 37 | 0.7 | 2.1 | 1.4 |
| Deep Learning | 75 | 38 | 37 | 0.7 | 2.1 | 1.4 |
| Cloud Computing | 111 | 43 | 68 | 0.4 | 1.7 | 1.3 |
| Trading | 111 | 43 | 68 | 0.4 | 1.7 | 1.3 |
| Swarm Robotics | 231 | 53 | 178 | 0.0 | 1.3 | 1.3 |

Per-batch top-10 industries and top-20 tags: `yc_industry_top_per_batch.csv`, `yc_tag_top_per_batch.csv`.

## 8. Category emergence classes

Rules (share-of-batch series over full batches; early = mean of first 2, late = mean of last 2): Emerging: late-early >= 2.0 pp and late >= 2.0x early and latest count >= 5. Declining: early >= 2.0% and late <= 0.5x early and early-late >= 2.0 pp. Spiky: peak >= 3.0x median and peak >= 2.0%. Persistent: mean >= 1.0% and CV <= 0.35. Else low-volume/mixed.

- Industries: Persistent 3, Spiky 2, Emerging 1, Low-volume / mixed 1, Declining 1.
  - Emerging: Industrials
  - Declining: Education
  - Spiky: Fintech, Government
  - Persistent: B2B, Healthcare, Consumer
- Subindustries: Low-volume / mixed 30, Spiky 14, Declining 7, Emerging 5, Persistent 2.
  - Emerging: B2B, B2B -> Infrastructure, Industrials -> Manufacturing and Robotics, Industrials, Industrials -> Defense
  - Declining: B2B -> Finance and Accounting, Healthcare -> Consumer Health and Wellness, Education, B2B -> Human Resources, Consumer -> Food and Beverage, Fintech -> Credit and Lending, Fintech -> Payments
  - Spiky: Fintech, Fintech -> Asset Management, Healthcare -> Drug Discovery and Delivery, Industrials -> Energy, Real Estate and Construction -> Construction, Real Estate and Construction -> Housing and Real Estate, Government, Industrials -> Climate, Fintech -> Banking and Exchange, Healthcare -> Therapeutics, B2B -> Recruiting and Talent, B2B -> Retail, Consumer -> Home and Personal, Healthcare -> Medical Devices
  - Persistent: B2B -> Engineering, Product and Design, B2B -> Productivity
- Tags: Low-volume / mixed 235, Spiky 38, Emerging 17, Declining 10, Persistent 3.
  - Emerging: Artificial Intelligence, AI, Robotics, Hard Tech, Hardware, Infrastructure, Manufacturing, Enterprise Software, Reinforcement Learning, Workflow Automation, Finance, Automation, Generative AI, Industrial, Defense (+2 more)
  - Declining: SaaS, Fintech, Marketplace, Consumer Health Services, Education, E-commerce, eLearning, Climate, Payments, Community
  - Spiky: Energy, Investing, Semiconductors, Aerospace, Drones, Deep Learning, Health & Wellness, Data Labeling, GovTech, Crypto / Web3, Data Science, Synthetic Biology, Conversational AI, DevOps, Design (+23 more)
  - Persistent: B2B, Developer Tools, Machine Learning

## 9. Taxonomy changes and other measurement risks

This is the most important caveat section. Several apparent trends are partly or wholly produced by how YC labels companies, not by which companies it funds.

1. **Retroactive relabeling is routine.** Across 24 monthly snapshots (2024-08-22 to 2026-09-01) there were 6500 label-change events on existing companies. The dominant flow is the pair 'Artificial Intelligence' <-> 'AI' (2632 swaps). Share of companies whose tag set changed between the first and latest snapshot, by batch (excluding pure AI/Artificial Intelligence swaps in the second column):

| batch | companies in both | % tags changed | % tags changed excl. AI swaps | % industry changed | % subindustry changed |
|---|---|---|---|---|---|
| Winter 2021 | 336 | 18.5 | 14.9 | 2.7 | 10.4 |
| Summer 2021 | 390 | 21.8 | 17.9 | 2.8 | 10.0 |
| Winter 2022 | 397 | 25.7 | 21.7 | 4.5 | 14.6 |
| Summer 2022 | 234 | 43.6 | 35.5 | 7.3 | 16.2 |
| Winter 2023 | 273 | 39.6 | 31.1 | 5.5 | 22.0 |
| Summer 2023 | 215 | 59.1 | 46.5 | 7.0 | 27.0 |
| Winter 2024 | 247 | 64.4 | 54.3 | 10.9 | 46.6 |
| Summer 2024 | 198 | 82.3 | 72.2 | 14.1 | 38.4 |

   Consequence: any tag-level 'first appearance' or share for older batches reflects today's labels applied retroactively, and the 'AI' vs 'Artificial Intelligence' split is unstable. Treat the two as one measurement with two names.
2. **New labels.** Tags with >= 5 companies that did not exist in the 2024-08-22 snapshot: Defense (first seen 2026-07-01, now 29). Subindustries added or removed: Industrials -> Defense (first 2026-01-01, last 2026-09-01, 0 -> 25). A label that appears in the vocabulary only recently can still be applied to companies from older batches; its first observed batch in section 6 is therefore not the first time such companies existed.
3. **Labels whose total count grew fastest across the whole directory between snapshots** (new companies plus relabeling): AI (410 -> 887), Artificial Intelligence (532 -> 990), B2B (931 -> 1120), Developer Tools (463 -> 549), AI Assistant (86 -> 160), Robotics (67 -> 140), Consumer (177 -> 249), Infrastructure (64 -> 130), Hardware (99 -> 160), Hard Tech (73 -> 132), Enterprise Software (74 -> 132), SaaS (1042 -> 1098).
4. **Near-duplicate labels** (kept separate everywhere in this analysis): API | APIs; Chatbot | Chatbots; E-Commerce | E-commerce; AI | Artificial Intelligence; Biotech | Biotechnology; Climate | ClimateTech; Cultivated Meat | Cultured Meat; Cultivated Meat | Clean Meat; Crypto / Web3 | Cryptocurrency; Machine Learning | ML; SaaS | Enterprise Software; Health Tech | Healthcare; Edtech | Education; Proptech | Real Estate; Conversational AI | Chatbot; AI Assistant | AI.
5. **Tag coverage collapses in some batches** (section 1): Winter 2026, Spring 2026. Unique-tag counts and tag shares there are not comparable.
6. **Parent-only subindustry strings are rising**: 'B2B' 8.7% -> 17.4%, 'Industrials' 0.1% -> 6.0%, 'Healthcare' 1.9% -> 5.1%, 'Consumer' 3.4% -> 2.6%, 'Fintech' 3.6% -> 2.6%, 'Government' 0.3% -> 0.9%, 'Education' 3.9% -> 0.4%, 'Real Estate and Construction' 0.0% -> 0.0%. Fewer child labels means child-level declines (e.g. within B2B) partly reflect less granular labelling.
7. **Secondary source disagreement.** The March-2026 dump agrees with today's directory on industry for 97.68% of shared companies but on the exact tag list for only 75.78%, consistent with point 1.
8. **Status and stage are point-in-time fields** (today's status for every company), and team size is today's team size, not size at batch.

## 10. Tag co-occurrence

**2021-2022** (1359 companies). Most frequent pairs: B2B + SaaS (206, lift 1.9); B2B + Fintech (84, lift 1.1); Fintech + SaaS (71, lift 0.9); AI + B2B (61, lift 1.3); Artificial Intelligence + B2B (55, lift 1.1); Artificial Intelligence + SaaS (52, lift 1.0); Developer Tools + SaaS (51, lift 1.4); AI + SaaS (50, lift 1.0). Highest lift with >= 8 co-occurrences: Sales + Sales Enablement (lift 26, n=10); Crypto / Web3 + DeFi (lift 24, n=8); Education + eLearning (lift 23, n=18); Biotech + Therapeutics (lift 22, n=11); Climate + ClimateTech (lift 21, n=10); Proptech + Real Estate (lift 20, n=12).

**2023-2024** (1084 companies). Most frequent pairs: B2B + SaaS (126, lift 2.2); AI + B2B (99, lift 1.2); Artificial Intelligence + B2B (99, lift 1.1); AI + Artificial Intelligence (68, lift 0.7); AI + SaaS (67, lift 1.0); Artificial Intelligence + SaaS (64, lift 1.0); Artificial Intelligence + Developer Tools (60, lift 1.2); AI + Developer Tools (58, lift 1.2). Highest lift with >= 8 co-occurrences: Legal + LegalTech (lift 50, n=9); Customer Success + Customer Support (lift 49, n=8); Biotech + Synthetic Biology (lift 34, n=11); Proptech + Real Estate (lift 32, n=8); Biotech + Therapeutics (lift 30, n=9); Logistics + Supply Chain (lift 21, n=10).

**2025-present** (1286 companies). Most frequent pairs: Artificial Intelligence + B2B (95, lift 1.8); AI + B2B (87, lift 1.9); Artificial Intelligence + Developer Tools (57, lift 2.0); B2B + SaaS (46, lift 2.7); AI + SaaS (43, lift 1.8); AI + Artificial Intelligence (38, lift 0.5); Artificial Intelligence + SaaS (37, lift 1.4); AI + Developer Tools (29, lift 1.1). Highest lift with >= 8 co-occurrences: AI-Enhanced Learning + Education (lift 70, n=9); Logistics + Supply Chain (lift 32, n=10); Health Tech + Healthcare (lift 21, n=11); Aerospace + Hard Tech (lift 17, n=11); Defense + Hard Tech (lift 13, n=8); Industrial + Manufacturing (lift 13, n=9).

- Strengthening (45 pairs): Artificial Intelligence + B2B (lift 1.1 -> 1.8); AI + B2B (lift 1.3 -> 1.9); Artificial Intelligence + Developer Tools (lift 1.4 -> 2.0); B2B + SaaS (lift 1.9 -> 2.7); AI + SaaS (lift 1.0 -> 1.8); AI + Fintech (lift 0.4 -> 2.1); Artificial Intelligence + Consumer (lift 0.8 -> 1.7); Artificial Intelligence + Fintech (lift 0.5 -> 1.3); B2B + Enterprise Software (lift 1.4 -> 2.0); Artificial Intelligence + Productivity (lift 1.4 -> 2.1).
- Weakening (19 pairs): AI + Artificial Intelligence (lift 1.4 -> 0.5); Developer Tools + Open Source (lift 7.5 -> 5.4); AI + Generative AI (lift 3.7 -> 1.6); B2B + Marketing (lift 2.6 -> 1.9); Artificial Intelligence + Generative AI (lift 2.3 -> 1.3); AI Assistant + Artificial Intelligence (lift 3.5 -> 1.3); AI + AI Assistant (lift 3.8 -> 1.4); Artificial Intelligence + Sales (lift 1.9 -> 1.4); Hard Tech + Hardware (lift 15.4 -> 7.2); AI + Marketing (lift 2.6 -> 1.6).
- Newly emerging (107 pairs): AI + Infrastructure (n=27, lift 1.8); Developer Tools + Infrastructure (n=26, lift 4.3); Artificial Intelligence + Infrastructure (n=25, lift 1.5); AI + Robotics (n=23, lift 1.5); Artificial Intelligence + Hardware (n=19, lift 1.4); Artificial Intelligence + Enterprise Software (n=19, lift 1.6); Artificial Intelligence + Automation (n=18, lift 2.2); Hardware + Robotics (n=16, lift 5.7); Artificial Intelligence + Robotics (n=15, lift 0.9); Artificial Intelligence + Reinforcement Learning (n=15, lift 1.8).

Full tables: `yc_tag_cooccurrence.csv`, `yc_tag_cooccurrence_change.csv`.

## 11. Geography (headquarters/location fields only)

- US share (regions contains 'United States of America'): 56.0% in Winter 2021 to 91.5% in Summer 2026; range across full batches 54.2%-92.8%.
- Any remote flag ('Remote', 'Fully Remote', 'Partly Remote'): 84.5% in Winter 2021 to 11.9% in Summer 2026.
- Distinct countries per batch: 41 in Winter 2021 to 14 in Summer 2026.
- Most common countries overall (companies): United States of America 2726, United Kingdom 154, India 128, Canada 72, France 56, Germany 53, Mexico 52, Singapore 41, Brazil 33, Nigeria 32.
  - India: 10.7% in Winter 2021 -> 0.4% in Summer 2026.
  - United Kingdom: 4.5% in Winter 2021 -> 2.1% in Summer 2026.
  - Canada: 3.6% in Winter 2021 -> 0.8% in Summer 2026.
  - Mexico: 3.6% in Winter 2021 -> 0.0% in Summer 2026.
- Macro-regions (YC `regions`): America / Canada 58.9% -> 92.3%; Europe 12.5% -> 4.3%; South Asia 11.0% -> 0.4%; Latin America 9.2% -> 0.8%; Southeast Asia 3.3% -> 0.8%; Africa 1.8% -> 0.0%; Middle East and North Africa 2.1% -> 0.4% (Winter 2021 -> Summer 2026).
- Cities (first entry of `all_locations`): San Francisco, USA 25.0% -> 73.6%; New York City, USA 13.1% -> 6.8%; London, United Kingdom 3.0% -> 2.1%; Bengaluru, India 5.1% -> 0.0%.

This describes where YC lists companies as located; it says nothing about target markets. Figure: `figures/geography_us_vs_non_us.png`.

## 12. Diversity and concentration

| batch | industries | subindustries | tags | tags per 150 cos | industry entropy (norm.) | industry HHI | top-5 industry % | tag entropy (norm.) | top-10 tag % of cos |
|---|---|---|---|---|---|---|---|---|---|
| Winter 2021 | 8 | 52 | 187 | 134.3 | 0.7 | 0.3 | 94.0 | 0.8 | 118.8 |
| Summer 2021 | 8 | 51 | 192 | 127.8 | 0.7 | 0.3 | 93.9 | 0.8 | 133.0 |
| Winter 2022 | 8 | 54 | 193 | 131.6 | 0.7 | 0.3 | 94.2 | 0.8 | 141.7 |
| Summer 2022 | 7 | 46 | 155 | 130.3 | 0.7 | 0.3 | 95.7 | 0.8 | 168.4 |
| Winter 2023 | 8 | 43 | 147 | 115.8 | 0.5 | 0.5 | 97.1 | 0.8 | 178.8 |
| Summer 2023 | 7 | 40 | 143 | 123.0 | 0.6 | 0.5 | 95.9 | 0.8 | 163.2 |
| Winter 2024 | 8 | 42 | 155 | 124.8 | 0.6 | 0.4 | 97.2 | 0.8 | 151.6 |
| Summer 2024 | 8 | 45 | 149 | 122.5 | 0.6 | 0.4 | 96.4 | 0.8 | 160.9 |
| Fall 2024 | 8 | 31 | 91 |  | 0.6 | 0.4 | 93.6 | 0.8 | 150.0 |
| Winter 2025 | 8 | 39 | 122 | 116.5 | 0.6 | 0.4 | 93.4 | 0.8 | 133.1 |
| Spring 2025 | 8 | 33 | 97 |  | 0.6 | 0.5 | 95.8 | 0.8 | 132.2 |
| Summer 2025 | 8 | 36 | 107 | 102.0 | 0.6 | 0.5 | 95.8 | 0.8 | 128.9 |
| Fall 2025 | 7 | 34 | 115 |  | 0.7 | 0.4 | 95.2 | 0.9 | 130.1 |
| Winter 2026 | 6 | 37 | 63 | 53.3 | 0.7 | 0.4 | 98.5 | 0.9 | 41.2 |
| Spring 2026 | 7 | 44 | 69 | 59.0 | 0.7 | 0.4 | 97.4 | 0.9 | 40.5 |
| Summer 2026 | 8 | 40 | 145 | 122.5 | 0.7 | 0.3 | 96.2 | 0.8 | 157.0 |

- Industry concentration: HHI 0.29 in Winter 2021 -> 0.34 in Summer 2026 (peak 0.50 in Summer 2023); normalised industry entropy 0.74 -> 0.66.
- Subindustry variety: 52 distinct strings in Winter 2021 -> 40 in Summer 2026 (batch sizes 336 and 235).
- Tag variety, size-adjusted (unique tags among 150 random companies): 134.3 in Winter 2021 -> 122.5 in Summer 2026; top-10 tags cover 118.8% of companies in Winter 2021 and 157.0% in Summer 2026.
- Reading: by industry the mix became markedly more concentrated in 2023-2025 (B2B alone above 60%) and has loosened somewhat in the most recent full batch as Industrials grew; by tag, size-adjusted variety is lower than in 2021 while the top-10 tags cover a larger slice of companies. Figures: `figures/industry_concentration_over_time.png`, `figures/tag_diversity_over_time.png`.

## 13. Requests for Startups (YC's own stated interests)

Parsed 295 requests across 27 editions/versions from three eras: 10 numbered essays (2009-2014), 9 versions of the consolidated RFS page (2014-2024, one version per distinct content), and 8 seasonal editions (Summer 2024 onward). Sources: live page plus Wayback Machine captures; raw HTML in `data/raw/rfs/`, table in `yc_rfs_requests.csv`.

| era | edition | requests | first capture | last capture | partners named |
|---|---|---|---|---|---|
| consolidated | March 2014 | 11 | 20140701175550 | 20140701175550 | 0 |
| consolidated | July 2014 | 12 | 20140802045600 | 20140903221245 | 0 |
| consolidated | September 2014 | 22 | 20141003045747 | 20150809071536 | 0 |
| consolidated | August 2015 | 24 | 20150901100100 | 20160902230944 | 0 |
| consolidated | September 2016 | 25 | 20161003082811 | 20180305063455 | 0 |
| consolidated | March 2018 | 27 | 20180401145637 | 20200401232808 | 0 |
| consolidated | April 2020 | 21 | 20200508115524 | 20220207231405 | 0 |
| consolidated | undated version first captured 2022-03-02 | 21 | 20220302031222 | 20220601030654 | 0 |
| consolidated | undated version first captured 2022-07-01 | 20 | 20220701115057 | 20240204003328 | 0 |
| seasonal | Summer 2024 | 20 | 20240302111333 | 20250102172352 | 0 |
| seasonal | Winter 2025 | 9 | 20250102172352 | 20250102172352 | 0 |
| seasonal | Spring 2025 | 14 | 20250202012604 | 20250501031358 | 0 |
| seasonal | Summer 2025 | 14 | 20250601125436 | 20250704000742 | 0 |
| seasonal | Fall 2025 | 6 | 20250801091449 | 20260101122607 | 0 |
| seasonal | Spring 2026 | 10 | 20260203133656 | 20260402165521 | 0 |
| seasonal | Summer 2026 | 16 | 20260501000432 | 20260708135218 | 16 |
| seasonal | Fall 2026 | 13 | 20260807171507 | 20260906000000 | 13 |

Longest-lived consolidated-era categories (exact title match across versions): A.I. (9 versions, March 2014 to undated version first captured 2022-07-01); Education (9 versions, March 2014 to undated version first captured 2022-07-01); Energy (9 versions, March 2014 to undated version first captured 2022-07-01); Healthcare (9 versions, March 2014 to undated version first captured 2022-07-01); One Million Jobs (8 versions, July 2014 to undated version first captured 2022-07-01); Diversity (7 versions, September 2014 to undated version first captured 2022-07-01); Enterprise Software (7 versions, September 2014 to undated version first captured 2022-07-01); Financial Services (7 versions, September 2014 to undated version first captured 2022-07-01); VR and AR (7 versions, September 2014 to undated version first captured 2022-07-01); Robotics (6 versions, March 2014 to March 2018).

Seasonal edition titles:

- **Summer 2024** (20): A way to end cancer; AI to build enterprise software; Applying machine learning to robotics; Better enterprise glue; Bring manufacturing back to America; Climate tech; Commercial open source companies; Developer tools inspired by existing internal tools; Eliminating middlemen in healthcare; Explainable AI; Foundation models for biological systems; LLMs for manual back office processes in legacy enterprises; New Enterprise Resource Planning software; New defense technology; New space companies; Small fine-tuned models as an alternative to giant generic ones; Spatial computing; Stablecoin finance; The Managed Service Organization model for healthcare; Using machine learning to simulate the physical world.
- **Winter 2025** (9): AI-aided engineering tools; Fintech 2.0; Government software; LLMs for chip design; Manufacture in the USA; New space companies; One million jobs 2.0; Public safety technology; Stablecoins 2.0.
- **Spring 2025** (14): A Secure AI App Store; AI Coding Agents for Hardware-Optimized Code; AI Commercial Open Source Software (AICOSS); AI Personal Staff for Everyone; B2A: Software Where the Customers Will All Be Agents; Browser & Computer Automation; Compliance and Audit; Datacenters; Devtools for AI Agents; DocuSign 2.0; Inference AI Infrastructure in the World of Test-Time Compute; Startup Founders with Systems Programming Expertise; The Future of Software Engineering; Vertical AI Agents.
- **Summer 2025** (14): AI Personal Assistant; AI Personal Tutor for Everyone; AI Research Labs; AI Residential Security; AI Voice Assistants for Email; AI for Personal Finance; AI for Scientific Advancement; Full-stack AI Companies; Healthcare AI; Internal Agent Builder; More Design Founders; Software Tools To Make Robots; The Future of Education; Voice AI.
- **Fall 2025** (6): AI Native Enterprise Software; Infrastructure for Multi-Agent Systems; Retraining Workers for the AI Economy; The First 10-person, $100B Company; Using LLMs Instead of Government Consulting; Video Generation as a Primitive.
- **Spring 2026** (10): AI Guidance for Physical Work; AI for Government; AI-Native Agencies; AI-Native Hedge Funds; Cursor for Product Managers; Modern Metal Mills; Stablecoin Financial Services; Infra for Government Fraud Hunters; Large Spatial Models; Make LLMs Easy to Train.
- **Summer 2026** (16): AI Personalized Medicine; AI for Low-Pesticide Agriculture; AI-Native Discovery Engines; AI-Native Service Companies; Company Brain; Counter-Swarm Defense; Dynamic Software Interfaces; Electronics in Space; Hardware Supply Chain; Industrial Capabilities in Space; Inference Chips for Agent Workflows; SaaS Challengers; Software for Agents; Startups That Want to Sell to Huge Companies; Supply Chain 2.0 for Semiconductors; The AI Operating System for Companies.
- **Fall 2026** (13): A Cloud for Small Software; AI for the Aging Population; AI-Native Compliance Infrastructure; AI-Powered Consumer Products for 1 Billion People; Compute at Sea; Data for the Real World; Multiplayer AI; New Operating Systems for the Physical World; Proving You're Human; Self-Maintaining APIs; The Best Time to Build in Crypto; The Future of American Defense; The Primer.

**YC label names appearing verbatim in RFS text** (exact, case-insensitive string match of tag / industry / subindustry names in request title+body; this is a lexical overlap, not a classification). Seasonal editions, requests mentioning: tags: AI 67, Infrastructure 15, Design 12, Compliance 10, APIs 8, Hardware 8, Robotics 8, Industrial 7, Consumer 7, Healthcare 7, Operations 7, Finance 6, Enterprise 6, Video 6, Payments 5, Documents 5, Travel 5, Insurance 5, Manufacturing 5, Sales 5. Subindustry children: Infrastructure 15, Operations 7, Payments 5, Insurance 5, Sales 5, Construction 4, Energy 4, Legal 4, Defense 3, Social 2.

For labels mentioned in a seasonal edition, share of batch in the two full batches before vs from the edition onward (descriptive; no causal reading):

| label | edition | requests | before | share before | after | share after | pp |
|---|---|---|---|---|---|---|---|
| Robotics | Summer 2026 | 1 | Summer 2025|Fall 2025 | 4.6 | Summer 2026 | 11.9 | 7.3 |
| AI | Summer 2024 | 5 | Summer 2023|Winter 2024 | 29.6 | Summer 2024|Fall 2024 | 35.4 | 5.8 |
| Hardware | Summer 2026 | 2 | Summer 2025|Fall 2025 | 3.5 | Summer 2026 | 8.5 | 5.0 |
| Hardware | Spring 2026 | 1 | Summer 2025|Fall 2025 | 3.5 | Summer 2026 | 8.5 | 5.0 |
| B2B | Fall 2025 | 1 | Spring 2025|Summer 2025 | 19.0 | Fall 2025|Summer 2026 | 23.6 | 4.6 |
| Manufacturing | Summer 2026 | 1 | Summer 2025|Fall 2025 | 2.6 | Summer 2026 | 6.8 | 4.2 |
| Manufacturing | Spring 2026 | 1 | Summer 2025|Fall 2025 | 2.6 | Summer 2026 | 6.8 | 4.2 |
| Energy | Spring 2026 | 1 | Summer 2025|Fall 2025 | 0.0 | Summer 2026 | 3.8 | 3.8 |
| B2B | Summer 2025 | 1 | Winter 2025|Spring 2025 | 19.0 | Summer 2025|Fall 2025 | 22.3 | 3.2 |
| AI | Fall 2025 | 5 | Spring 2025|Summer 2025 | 28.7 | Fall 2025|Summer 2026 | 31.8 | 3.2 |
| Semiconductors | Summer 2026 | 1 | Summer 2025|Fall 2025 | 0.0 | Summer 2026 | 3.0 | 3.0 |
| Productivity | Spring 2025 | 1 | Fall 2024|Winter 2025 | 1.7 | Spring 2025|Summer 2025 | 4.5 | 2.8 |
| Infrastructure | Spring 2026 | 1 | Summer 2025|Fall 2025 | 5.4 | Summer 2026 | 8.1 | 2.7 |
| Healthcare | Spring 2026 | 1 | Summer 2025|Fall 2025 | 2.0 | Summer 2026 | 4.7 | 2.7 |
| Healthcare | Summer 2026 | 1 | Summer 2025|Fall 2025 | 2.0 | Summer 2026 | 4.7 | 2.7 |

Figures: `figures/rfs_requests_per_edition.png`, `figures/rfs_tag_name_mentions_by_edition.png`.

## 14. Prior work checked

- yc-oss/api (used): the only maintained, complete, daily-updated dump of YC's public directory with tags/industries back to 2005; its git history (Aug 2024 onward) is what enables the taxonomy-change checks above. START_YEAR can be set to 2005 without any code change.
- EXTREMOPHILARUM/yc-dataset (used for enrichment): 5,758-company snapshot (Mar 2026) with founders, launches, news, and 173 post-mortems; lower coverage than yc-oss/api.
- corralm/yc-scraper + Kaggle 'Y Combinator Directory' (Oct 2025, ~4,000 companies, founder fields), Kaggle 'Complete YCombinator Dataset 2005-2024', RummageLabs S24/F24 sets, benstaf/ycbench (W26 only), Apify scrapers (paid, same Algolia data), Extruct 'YC S25' post (one batch): none publishes a longitudinal analysis of YC's native taxonomy; none adds label information beyond the Algolia index.
- RFS: no structured multi-year dataset exists (the Hugging Face 'yc-rfs-analysis-2026' repo is empty); the table here was built from Wayback captures.

## 15. Questions YC's native taxonomy cannot answer

These require reading company descriptions (a future semantic/LLM classification phase) and are deliberately not attempted here:

- Whether a company is 'software' or 'deep tech'/'hard tech' in a consistent sense: 'Hard Tech' is a tag applied unevenly and retroactively, and Industrials includes pure-software companies.
- Whether a company is AI-native versus AI-adjacent, or which AI modality it uses: 'AI'/'Artificial Intelligence' now covers a third of every batch and is swapped between two names.
- Whether a company builds physical hardware, robots, or devices, versus software for those industries (e.g. 'Manufacturing and Robotics' contains both).
- Target customer or end market (regulated industry, SMB vs enterprise, consumer segment) and target geography: only headquarters location is available.
- Business model (SaaS vs marketplace vs services vs hardware sales) beyond the self-applied 'SaaS'/'Marketplace' tags, whose usage collapsed after 2023.
- Whether a company matches a specific RFS request or theme (the string overlap in section 13 is lexical only).
- Defense or dual-use exposure beyond the new 'Defense' label (introduced in the directory in 2026 and applied to 29 companies).
- Any measure that needs the 661 zero-tag companies (18%) to be classified, especially in Winter/Spring 2026.
- Founder background, technical depth, or 'research-lab' origin: not in the directory at all.
- Stage/traction at the time of the batch: status, stage and team size are today's values.
