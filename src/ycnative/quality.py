"""Data-quality report and a programmatic spot check of exported rows against the raw JSON."""
from __future__ import annotations
import json, random
import pandas as pd
from .config import ROOT

def dq_report(df_all, df, excluded, bs, tax_summary, xc, low_tag_batches, cfg):
    rows = [
        ("companies_in_source", len(df_all)), ("companies_selected", len(df)), ("companies_excluded_by_window_or_batch", len(excluded)),
        ("start_year", cfg["START_YEAR"]), ("end_year", cfg["END_YEAR"] or "latest"), ("min_full_batch", cfg["MIN_FULL_BATCH"]),
        ("duplicate_ids_in_source", int(df_all["id"].duplicated().sum())), ("duplicate_slugs_in_source", int(df_all["slug"].duplicated().sum())),
        ("companies_with_former_names", int(df["former_names"].map(len).gt(0).sum())),
        ("malformed_or_unspecified_batch_values", "; ".join(f"{k}={v}" for k, v in df_all.loc[~df_all["n_batch_valid"], "batch"].value_counts().items()) or "none"),
        ("partial_batches", "; ".join(bs.loc[bs["is_partial_batch"], "batch"]) or "none"),
        ("low_tag_coverage_batches", "; ".join(low_tag_batches) or "none"),
        ("source_cross_check_mismatches", int((~xc["match"]).sum())), ("source_cross_check_rows", len(xc)),
    ] + list(tax_summary.items())
    return pd.DataFrame(rows, columns=["check", "value"])

def spot_check(df: pd.DataFrame, records: list[dict], n=50, seed=20260906) -> pd.DataFrame:
    by_id = {r["id"]: r for r in records}
    rng = random.Random(seed)
    ids = rng.sample(list(df["id"]), n)
    out = []
    fields = ["name", "slug", "batch", "website", "one_liner", "long_description", "team_size", "all_locations", "industry", "subindustry",
              "industries", "tags", "regions", "stage", "status", "isHiring", "nonprofit", "top_company", "launched_at", "former_names", "url"]
    d = df.set_index("id")
    for i in ids:
        raw, row = by_id[i], d.loc[i]
        for f in fields:
            a, b = raw.get(f), row[f]
            if isinstance(a, list): ok = list(a) == list(b)
            elif a is None: ok = (b is None) or (isinstance(b, float) and pd.isna(b))
            else: ok = (a == b) or (str(a) == str(b))
            out.append({"company_id": i, "slug": raw["slug"], "field": f, "raw_value": str(a)[:80], "exported_value": str(b)[:80], "match": bool(ok)})
        # derived fields
        season, year = (raw["batch"].split() + [None, None])[:2]
        out.append({"company_id": i, "slug": raw["slug"], "field": "n_year(derived)", "raw_value": year, "exported_value": str(row["n_year"]), "match": str(row["n_year"]) == str(year)})
        child = raw["subindustry"].split("->")[1].strip() if "->" in (raw["subindustry"] or "") else None
        out.append({"company_id": i, "slug": raw["slug"], "field": "n_subindustry_child(derived)", "raw_value": child, "exported_value": str(row["n_subindustry_child"]), "match": (row["n_subindustry_child"] == child) or (child is None and pd.isna(row["n_subindustry_child"]))})
        out.append({"company_id": i, "slug": raw["slug"], "field": "n_is_us(derived)", "raw_value": "United States of America" in raw["regions"], "exported_value": bool(row["n_is_us"]), "match": bool(row["n_is_us"]) == ("United States of America" in raw["regions"])})
    res = pd.DataFrame(out)
    return res
