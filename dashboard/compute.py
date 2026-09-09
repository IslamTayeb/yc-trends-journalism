"""Era-aware aggregations over the pipeline's long tables. Pure pandas, no UI."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

MEASURES = {
    "share": "Share of batch (%)",
    "tagged": "Share of tagged companies (%)",
    "count": "Count",
}


def _denominator(meta: pd.DataFrame, measure: str) -> pd.Series:
    col = "tagged_companies" if measure == "tagged" else "total_companies"
    return meta.set_index("batch")[col]


@st.cache_data(show_spinner=False)
def label_by_batch(long_df: pd.DataFrame, label_col: str, meta: pd.DataFrame, measure: str) -> pd.DataFrame:
    """Tidy label x batch table with count and share. Only observed (label, batch) pairs; use grid() to fill zeros."""
    counts = (long_df.groupby(["batch", label_col], observed=True)["company_id"].nunique()
              .rename("count").reset_index())
    denom = _denominator(meta, measure).rename("total").reset_index()
    out = counts.merge(denom, on="batch", how="left")
    out["share_pct"] = np.where(out["total"] > 0, out["count"] / out["total"] * 100, np.nan).round(2)
    out = out.merge(meta[["batch", "batch_code", "batch_order", "pos", "is_partial_batch", "low_tag_coverage"]],
                    on="batch", how="left")
    return out.sort_values(["batch_order", label_col]).reset_index(drop=True)


def grid(by_batch: pd.DataFrame, label_col: str, labels: list[str], meta: pd.DataFrame) -> pd.DataFrame:
    """Complete label x batch grid for the chosen labels (zeros where absent)."""
    idx = pd.MultiIndex.from_product([labels, meta["batch"]], names=[label_col, "batch"])
    sub = by_batch[by_batch[label_col].isin(labels)].set_index([label_col, "batch"])
    g = sub.reindex(idx).reset_index()
    fill = meta.set_index("batch")
    for c in ["batch_code", "batch_order", "pos", "is_partial_batch", "low_tag_coverage", "total_companies"]:
        g[c] = g["batch"].map(fill[c])
    g["count"] = g["count"].fillna(0).astype(int)
    g["total"] = g["total"].fillna(g["total_companies"])
    g["share_pct"] = g["share_pct"].fillna(0.0)
    g[label_col] = pd.Categorical(g[label_col], categories=labels, ordered=True)
    return g.sort_values([label_col, "batch_order"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def era_totals(companies: pd.DataFrame, measure: str, exclude_batches: tuple[str, ...]) -> pd.Series:
    c = companies[~companies["batch"].isin(exclude_batches)]
    if measure == "tagged":
        c = c[c["n_n_tags"] > 0]
    return c.groupby("era", observed=True)["id"].nunique()


@st.cache_data(show_spinner=False)
def label_by_era(long_df: pd.DataFrame, label_col: str, companies: pd.DataFrame, measure: str,
                 exclude_batches: tuple[str, ...]) -> pd.DataFrame:
    """label x era counts and shares. `long_df` and `companies` must carry an `era` column."""
    sub = long_df[~long_df["batch"].isin(exclude_batches)]
    counts = (sub.groupby(["era", label_col], observed=True)["company_id"].nunique()
              .rename("count").reset_index())
    totals = era_totals(companies, measure, exclude_batches).rename("total").reset_index()
    out = counts.merge(totals, on="era", how="left")
    out["share_pct"] = (out["count"] / out["total"] * 100).round(2)
    return out


def era_wide(by_era: pd.DataFrame, label_col: str, eras_order: list[str], value: str = "share_pct") -> pd.DataFrame:
    w = by_era.pivot_table(index=label_col, columns="era", values=value, aggfunc="first", observed=True)
    w = w.reindex(columns=[e for e in eras_order if e in w.columns]).fillna(0)
    w.columns.name = None
    return w


def era_compare(by_era: pd.DataFrame, label_col: str, era_a: str, era_b: str, min_count: int = 0) -> pd.DataFrame:
    a = by_era[by_era["era"] == era_a].set_index(label_col)[["count", "share_pct"]]
    b = by_era[by_era["era"] == era_b].set_index(label_col)[["count", "share_pct"]]
    j = a.join(b, how="outer", lsuffix="_a", rsuffix="_b").fillna(0)
    j = j[(j["count_a"] >= min_count) | (j["count_b"] >= min_count)]
    j["pp_change"] = (j["share_pct_b"] - j["share_pct_a"]).round(2)
    j["ratio"] = np.where(j["share_pct_a"] > 0, j["share_pct_b"] / j["share_pct_a"], np.nan)
    j["ratio"] = j["ratio"].round(2)
    j = j.rename(columns={"count_a": f"count · {era_a}", "share_pct_a": f"share % · {era_a}",
                          "count_b": f"count · {era_b}", "share_pct_b": f"share % · {era_b}"})
    for c in j.columns:
        if c.startswith("count"):
            j[c] = j[c].astype(int)
    return j.sort_values("pp_change", ascending=False).reset_index()


def top_per_batch(by_batch: pd.DataFrame, label_col: str, n: int) -> pd.DataFrame:
    d = by_batch.sort_values(["batch_order", "count"], ascending=[True, False]).copy()
    d["rank"] = d.groupby("batch")["count"].rank(method="first", ascending=False).astype(int)
    return d[d["rank"] <= n].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def cooccurrence_by_era(tags: pd.DataFrame, min_tag_companies: int, min_pair_count: int,
                        exclude_batches: tuple[str, ...]) -> pd.DataFrame:
    """Tag pair counts, Jaccard and lift per era (same definitions as src/ycnative/cooccurrence.py)."""
    rows = []
    sub = tags[~tags["batch"].isin(exclude_batches)]
    for era, g in sub.groupby("era", observed=True):
        pairs = g[["company_id", "tag"]].drop_duplicates()
        n = pairs["company_id"].nunique()
        tag_n = pairs["tag"].value_counts()
        keep = tag_n[tag_n >= min_tag_companies].index
        pairs = pairs[pairs["tag"].isin(keep)]
        if pairs.empty:
            continue
        x = pd.crosstab(pairs["company_id"], pairs["tag"]).clip(upper=1)
        m = x.T.values @ x.values
        labels = list(x.columns)
        iu = np.triu_indices(len(labels), k=1)
        for i, j in zip(*iu):
            c = int(m[i, j])
            if c < min_pair_count:
                continue
            ca, cb = int(tag_n[labels[i]]), int(tag_n[labels[j]])
            expected = ca * cb / n
            rows.append({
                "era": era, "tag_a": labels[i], "tag_b": labels[j], "count_a": ca, "count_b": cb,
                "cooccurrence": c, "era_companies": n,
                "jaccard": round(c / (ca + cb - c), 4),
                "lift": round(c / expected, 3) if expected else np.nan,
                "expected": round(expected, 2),
            })
    cols = ["era", "tag_a", "tag_b", "count_a", "count_b", "cooccurrence", "era_companies", "jaccard", "lift", "expected"]
    return pd.DataFrame(rows, columns=cols)


def pair_change(cooc: pd.DataFrame, era_a: str, era_b: str, new_pair_max_early: int = 2,
                min_pair_count: int = 5, lift_delta: float = 0.5) -> pd.DataFrame:
    a = cooc[cooc["era"] == era_a].set_index(["tag_a", "tag_b"])[["cooccurrence", "jaccard", "lift"]]
    b = cooc[cooc["era"] == era_b].set_index(["tag_a", "tag_b"])[["cooccurrence", "jaccard", "lift"]]
    j = a.join(b, how="outer", lsuffix="_a", rsuffix="_b")
    j[["cooccurrence_a", "cooccurrence_b"]] = j[["cooccurrence_a", "cooccurrence_b"]].fillna(0).astype(int)
    j["lift_change"] = (j["lift_b"] - j["lift_a"]).round(3)

    def rel(r):
        if r["cooccurrence_a"] <= new_pair_max_early and r["cooccurrence_b"] >= min_pair_count:
            return "newly emerging"
        if r["cooccurrence_b"] <= new_pair_max_early and r["cooccurrence_a"] >= min_pair_count:
            return "disappeared"
        if pd.isna(r["lift_change"]):
            return "present in one era only"
        if r["lift_change"] >= lift_delta:
            return "strengthening"
        if r["lift_change"] <= -lift_delta:
            return "weakening"
        return "stable"

    j["relationship"] = j.apply(rel, axis=1)
    return j.reset_index().rename(columns={
        "cooccurrence_a": f"co-occurrence · {era_a}", "cooccurrence_b": f"co-occurrence · {era_b}",
        "jaccard_a": f"jaccard · {era_a}", "jaccard_b": f"jaccard · {era_b}",
        "lift_a": f"lift · {era_a}", "lift_b": f"lift · {era_b}",
    })


@st.cache_data(show_spinner=False)
def era_summary(companies: pd.DataFrame, industries: pd.DataFrame, meta: pd.DataFrame,
                eras_order: list[str], top_n: int = 5) -> pd.DataFrame:
    rows = []
    for era in eras_order:
        c = companies[companies["era"] == era]
        if c.empty:
            continue
        m = meta[meta["era"] == era]
        ind = industries[(industries["era"] == era) & (industries["level"] == "top")]
        top = (ind.groupby("industry")["company_id"].nunique().sort_values(ascending=False).head(top_n))
        top_txt = ", ".join(f"{k} {v / len(c) * 100:.0f}%" for k, v in top.items())
        rows.append({
            "era": era,
            "batches": f"{m.iloc[0]['batch_code']} – {m.iloc[-1]['batch_code']}" if len(m) else "",
            "n_batches": int(len(m)),
            "companies": int(len(c)),
            "companies_per_batch": round(len(c) / max(len(m), 1), 1),
            "us_share_pct": round(c["n_is_us"].astype(float).mean() * 100, 1),
            "remote_share_pct": round(c["n_is_remote"].astype(float).mean() * 100, 1),
            "median_team_size": c["team_size"].median(),
            "zero_tag_pct": round((c["n_n_tags"] == 0).mean() * 100, 1),
            "partial_batches": int(m["is_partial_batch"].sum()),
            "low_tag_coverage_batches": int(m["low_tag_coverage"].sum()),
            f"top {top_n} industries (share of era)": top_txt,
        })
    return pd.DataFrame(rows)


def geo_by_era(companies: pd.DataFrame, geo_long: pd.DataFrame, key: str, eras_order: list[str],
               exclude_batches: tuple[str, ...]) -> pd.DataFrame:
    """Share of era companies per region/country. geo_long has batch-level counts from the pipeline."""
    tot = era_totals(companies, "share", exclude_batches)
    g = geo_long[~geo_long["batch"].isin(exclude_batches)]
    s = g.groupby(["era", key], observed=True)["count"].sum().reset_index()
    s["total"] = s["era"].map(tot)
    s["share_pct"] = (s["count"] / s["total"] * 100).round(2)
    s["era"] = pd.Categorical(s["era"], categories=eras_order, ordered=True)
    return s.sort_values(["era", "count"], ascending=[True, False]).reset_index(drop=True)


def numeric_by_era(df: pd.DataFrame, cols: list[str], eras_order: list[str], exclude_batches: tuple[str, ...]) -> pd.DataFrame:
    """Mean of batch-level metrics per era (used for diversity and geography trend tables)."""
    d = df[~df["batch"].isin(exclude_batches)]
    out = d.groupby("era", observed=True)[cols].mean().round(3)
    out["n_batches"] = d.groupby("era", observed=True)["batch"].nunique()
    return out.reindex([e for e in eras_order if e in out.index]).reset_index()
