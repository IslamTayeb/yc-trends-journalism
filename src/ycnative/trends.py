"""Generic category x batch matrices and per-category trend statistics."""
from __future__ import annotations
import numpy as np, pandas as pd
from .emergence import classify

def matrices(long_df: pd.DataFrame, label_col: str, df: pd.DataFrame, batches: list[str]):
    """counts (label x batch) and shares (% of ALL companies in batch)."""
    sizes = df.groupby("batch").size().reindex(batches).fillna(0)
    counts = (long_df.drop_duplicates(["company_id", label_col]).groupby([label_col, "batch"]).size()
              .unstack("batch").reindex(columns=batches).fillna(0).astype(int))
    shares = (100 * counts / sizes).round(3)
    return counts, shares, sizes

def matrices_of_tagged(long_df: pd.DataFrame, label_col: str, df: pd.DataFrame, batches: list[str]):
    """shares with denominator = companies in batch that have >=1 tag (robust to batches where tags are missing)."""
    sizes = df[df["n_n_tags"] > 0].groupby("batch").size().reindex(batches).fillna(0)
    counts = (long_df.drop_duplicates(["company_id", label_col]).groupby([label_col, "batch"]).size()
              .unstack("batch").reindex(columns=batches).fillna(0).astype(int))
    return counts, (100 * counts / sizes.replace(0, np.nan)).round(3), sizes

def year_matrices(long_df: pd.DataFrame, label_col: str, df: pd.DataFrame):
    years = sorted(df["n_year"].unique())
    sizes = df.groupby("n_year").size().reindex(years)
    counts = (long_df.drop_duplicates(["company_id", label_col]).groupby([label_col, "year"]).size()
              .unstack("year").reindex(columns=years).fillna(0).astype(int))
    return counts, (100 * counts / sizes).round(3), sizes

def to_long(counts, shares, label_name, batch_meta):
    c = counts.stack().rename("count").reset_index().rename(columns={"level_0": label_name, counts.index.name or "index": label_name})
    s = shares.stack().rename("share_pct").reset_index()
    c.columns = [label_name, "batch", "count"]; s.columns = [label_name, "batch", "share_pct"]
    out = c.merge(s, on=[label_name, "batch"]).merge(batch_meta, on="batch")
    return out.sort_values([label_name, "batch_order"]).reset_index(drop=True)

def trend_stats(counts: pd.DataFrame, shares: pd.DataFrame, batch_meta: pd.DataFrame, cfg: dict, label_name: str, exclude_batches: list[str] | None = None):
    """exclude_batches: batches dropped from "full batch" statistics (e.g. batches with unreliable tag coverage)."""
    bm = batch_meta.set_index("batch")
    batches = list(counts.columns)
    excl = set(exclude_batches or [])
    full = [b for b in batches if not bm.loc[b, "is_partial_batch"] and b not in excl]
    start_year = cfg["START_YEAR"]
    early_batches = [b for b in batches if bm.loc[b, "year"] == start_year] or batches[:1]
    latest = full[-1] if full else batches[-1]
    excluded_note = ",".join(sorted(excl)) if excl else ""
    sizes = bm["total_companies"]
    rows = []
    for lab in counts.index:
        c, s = counts.loc[lab], shares.loc[lab]
        nz = [b for b in batches if c[b] > 0]
        early_cnt = int(c[early_batches].sum()); early_den = int(sizes[early_batches].sum())
        early_share = 100 * early_cnt / early_den if early_den else np.nan
        peak_b = s[full].idxmax() if full else s.idxmax()
        r = {label_name: lab, "total_companies": int(c.sum()), "batches_excluded_from_stats": excluded_note,
             "first_observed_batch": nz[0] if nz else None, "latest_observed_batch": nz[-1] if nz else None,
             "n_batches_present": len(nz),
             "peak_batch": peak_b, "peak_count": int(c[peak_b]), "peak_share_pct": float(s[peak_b]),
             "earliest_year": start_year, "earliest_year_count": early_cnt, "earliest_year_share_pct": round(early_share, 3),
             "earliest_batch_share_pct": float(s[batches[0]]),
             "latest_full_batch": latest, "latest_count": int(c[latest]), "latest_share_pct": float(s[latest]),
             "count_change": int(c[latest]) - int(c[early_batches[0]]) if early_batches else None,
             "count_change_vs_earliest_year_avg": round(float(c[latest]) - early_cnt / len(early_batches), 2),
             "pp_change": round(float(s[latest]) - early_share, 3),
             "rolling3_latest_share_pct": round(float(s[full].rolling(3, min_periods=1).mean().iloc[-1]), 3) if full else None,
             "mean_share_full_batches_pct": round(float(s[full].mean()), 3) if full else None,
             "newly_appearing": bool(nz and bm.loc[nz[0], "batch_order"] > bm.loc[batches[0], "batch_order"] and c.sum() >= cfg["NEW_LABEL_MIN_COUNT"]),
             }
        # peaked-then-declined: peak in a full batch that is not among last 2 full batches, and latest <= half of peak
        r["peaked_then_declined"] = bool(full and peak_b not in full[-2:] and s[peak_b] > 0 and s[latest] <= 0.5 * s[peak_b] and c[peak_b] >= cfg["NEW_LABEL_MIN_COUNT"])
        r.update(classify(s[full].values if full else s.values, c[full].values if full else c.values, cfg["EMERGENCE"]))
        rows.append(r)
    out = pd.DataFrame(rows)
    out["rank_latest"] = out["latest_share_pct"].rank(ascending=False, method="min").astype(int)
    out["rank_earliest_year"] = out["earliest_year_share_pct"].rank(ascending=False, method="min").astype(int)
    out["rank_change"] = out["rank_earliest_year"] - out["rank_latest"]
    return out.sort_values("latest_share_pct", ascending=False).reset_index(drop=True)
