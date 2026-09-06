"""Category diversity / concentration per batch."""
from __future__ import annotations
import numpy as np, pandas as pd

def entropy(p: np.ndarray):
    p = p[p > 0]; return float(-(p * np.log(p)).sum())

def diversity(df: pd.DataFrame, batch_meta: pd.DataFrame, cfg: dict):
    rng = np.random.default_rng(cfg["RANDOM_SEED"])
    rows = []
    for b, g in df.groupby("batch", sort=False):
        n = len(g)
        ind = g["n_industry_top"].value_counts(); pi = (ind / ind.sum()).values
        tags = g["n_tags_norm"].explode().dropna(); tc = tags.value_counts(); pt = (tc / tc.sum()).values
        r = {"batch": b, "total_companies": n,
             "unique_industries": int(g["n_industry_top"].nunique()),
             "unique_subindustries": int(g["n_subindustry_full"].nunique()),
             "unique_tags": int(tc.size),
             "tag_assignments": int(tc.sum()), "mean_tags_per_company": round(g["n_n_tags"].mean(), 3),
             "industry_entropy": round(entropy(pi), 4), "industry_entropy_normalised": round(entropy(pi) / np.log(len(pi)), 4) if len(pi) > 1 else 0.0,
             "tag_entropy": round(entropy(pt), 4) if pt.size else None, "tag_entropy_normalised": round(entropy(pt) / np.log(len(pt)), 4) if len(pt) > 1 else None,
             "industry_hhi": round(float((pi ** 2).sum()), 4), "tag_hhi": round(float((pt ** 2).sum()), 5) if pt.size else None,
             "top5_industry_share_pct": round(100 * ind.head(5).sum() / n, 2),
             "top10_tag_share_pct_of_companies": round(100 * tc.head(10).sum() / n, 2),
             "top10_tag_share_pct_of_assignments": round(100 * tc.head(10).sum() / tc.sum(), 2) if tc.sum() else None}
        # rarefied tag richness: mean unique tags among RAREFY_N random companies
        N = cfg["RAREFY_N"]
        if n >= N:
            lists = g["n_tags_norm"].tolist(); vals = []
            for _ in range(cfg["RAREFY_DRAWS"]):
                idx = rng.choice(n, N, replace=False); vals.append(len({t for i in idx for t in lists[i]}))
            r["rarefied_unique_tags"] = round(float(np.mean(vals)), 2)
        else:
            r["rarefied_unique_tags"] = None
        rows.append(r)
    return pd.DataFrame(rows).merge(batch_meta[["batch", "batch_order", "is_partial_batch"]], on="batch").sort_values("batch_order").reset_index(drop=True)
