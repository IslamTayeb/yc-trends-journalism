"""Tag co-occurrence per period: counts, Jaccard, lift; strengthening/weakening/new pairs."""
from __future__ import annotations
import numpy as np, pandas as pd

def period_of(year: int, periods: list[dict]) -> str | None:
    for p in periods:
        if p["start"] <= year <= p["end"]:
            return p["label"]
    return None

def cooccurrence(df: pd.DataFrame, cfg: dict):
    periods = cfg["PERIODS"]
    df = df.assign(period=df["n_year"].map(lambda y: period_of(int(y), periods)))
    out = []
    for p in periods:
        g = df[df["period"] == p["label"]]
        n = len(g)
        tl = g[["id", "n_tags_norm"]].explode("n_tags_norm").dropna().drop_duplicates().reset_index(drop=True)
        keep = tl["n_tags_norm"].value_counts()
        keep = keep[keep >= cfg["COOC_MIN_TAG_COMPANIES"]].index
        tl = tl[tl["n_tags_norm"].isin(keep)]
        if tl.empty: continue
        M = pd.crosstab(tl["id"], tl["n_tags_norm"]).astype(int)
        co = M.T @ M
        tags = list(co.index); freq = np.diag(co.values)
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                ab = int(co.iat[i, j])
                if ab < cfg["COOC_MIN_PAIR_COUNT"]: continue
                a, b = int(freq[i]), int(freq[j])
                out.append({"period": p["label"], "tag_a": tags[i], "tag_b": tags[j], "count_a": a, "count_b": b, "cooccurrence": ab,
                            "period_companies": n, "jaccard": round(ab / (a + b - ab), 4),
                            "lift": round((ab / n) / ((a / n) * (b / n)), 3), "expected": round(a * b / n, 2)})
    pairs = pd.DataFrame(out)
    if pairs.empty:
        return pairs, pd.DataFrame()
    first, last = periods[0]["label"], periods[-1]["label"]
    w = pairs.pivot_table(index=["tag_a", "tag_b"], columns="period", values=["cooccurrence", "lift", "jaccard"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    cf, cl = f"cooccurrence_{first}", f"cooccurrence_{last}"
    lf, ll = f"lift_{first}", f"lift_{last}"
    for c in (cf, cl, lf, ll):
        if c not in w: w[c] = np.nan
    w["lift_change"] = w[ll] - w[lf]
    w["relationship"] = np.select(
        [w[cf].isna() & w[cl].notna(), w[cl].isna() & w[cf].notna(), w["lift_change"] >= 0.5, w["lift_change"] <= -0.5],
        ["newly emerging", "disappeared", "strengthening", "weakening"], default="stable")
    return pairs.sort_values(["period", "cooccurrence"], ascending=[True, False]).reset_index(drop=True), w
