"""Top-N categories per batch and rank comparison earliest year vs latest full batch."""
from __future__ import annotations
import pandas as pd

def top_n_per_batch(shares: pd.DataFrame, counts: pd.DataFrame, n: int, label_name: str) -> pd.DataFrame:
    rows = []
    for b in shares.columns:
        s = shares[b].sort_values(ascending=False).head(n)
        for rank, (lab, val) in enumerate(s.items(), 1):
            rows.append({"batch": b, "rank": rank, label_name: lab, "share_pct": float(val), "count": int(counts.loc[lab, b])})
    return pd.DataFrame(rows)

def rank_table(stats: pd.DataFrame, label_name: str, cfg: dict) -> pd.DataFrame:
    t = stats[[label_name, "rank_earliest_year", "rank_latest", "rank_change", "earliest_year_share_pct", "latest_share_pct", "pp_change",
               "earliest_year_count", "latest_count", "latest_full_batch"]].copy()
    t["major_mover"] = (t["rank_change"].abs() >= cfg["MAJOR_MOVER_RANK_CHANGE"]) | (t["pp_change"].abs() >= cfg["MAJOR_MOVER_PP"])
    return t.sort_values("rank_latest").reset_index(drop=True)
