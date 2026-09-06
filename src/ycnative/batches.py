"""Per-batch summary."""
from __future__ import annotations
import pandas as pd

def batch_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    statuses = sorted(df["n_status_norm"].dropna().unique())
    for b, g in df.groupby("batch", sort=False):
        r = {"batch": b, "batch_code": g["n_batch_code"].iloc[0], "year": int(g["n_year"].iloc[0]),
             "season": g["n_batch_season"].iloc[0], "batch_order": int(g["n_batch_order"].iloc[0]),
             "total_companies": len(g), "is_partial_batch": bool(g["n_batch_is_partial"].iloc[0])}
        for s in statuses:
            r[f"status_{s.lower().replace(' ','_')}"] = int((g["n_status_norm"] == s).sum())
        r["hiring_companies"] = int(g["isHiring"].fillna(False).astype(bool).sum())
        r["nonprofit_companies"] = int(g["nonprofit"].fillna(False).astype(bool).sum())
        r["top_companies"] = int(g["top_company"].fillna(False).astype(bool).sum())
        ts = pd.to_numeric(g["team_size"], errors="coerce")
        r["median_team_size"] = float(ts.median()) if ts.notna().any() else None
        r["mean_team_size"] = round(float(ts.mean()), 2) if ts.notna().any() else None
        r["missing_team_size_pct"] = round(100 * ts.isna().mean(), 2)
        r["zero_tag_companies"] = int((g["n_n_tags"] == 0).sum())
        r["missing_industry_companies"] = int(g["n_industry_top"].isna().sum())
        r["missing_description_companies"] = int((~g["n_has_description"]).sum())
        r["us_companies"] = int(g["n_is_us"].sum()); r["us_share_pct"] = round(100 * g["n_is_us"].mean(), 2)
        r["remote_companies"] = int(g["n_is_remote"].sum()); r["remote_share_pct"] = round(100 * g["n_is_remote"].mean(), 2)
        rows.append(r)
    return pd.DataFrame(rows).sort_values("batch_order").reset_index(drop=True)
