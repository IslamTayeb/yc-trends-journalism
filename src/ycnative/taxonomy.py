"""Enumerate YC's taxonomy as present in the selected data, and cross-check against the source's own lists."""
from __future__ import annotations
import json, pathlib
import pandas as pd
from .config import RAW

def inventory(df: pd.DataFrame, tags_long: pd.DataFrame, inds_long: pd.DataFrame, subs_long: pd.DataFrame):
    n = len(df)
    industries = (df.groupby("n_industry_top").size().rename("companies").reset_index()
                  .rename(columns={"n_industry_top": "industry"}).sort_values("companies", ascending=False))
    industries["share_pct"] = (100 * industries["companies"] / n).round(2)
    subs = (subs_long.groupby(["industry", "subindustry", "subindustry_child"], dropna=False).size().rename("companies")
            .reset_index().sort_values("companies", ascending=False))
    subs["share_pct"] = (100 * subs["companies"] / n).round(2)
    inds_arr = inds_long.groupby(["industry", "level"]).size().rename("companies").reset_index().sort_values("companies", ascending=False)
    tags = tags_long.groupby("tag").size().rename("companies").reset_index().sort_values("companies", ascending=False)
    tags["share_pct"] = (100 * tags["companies"] / n).round(2)
    tags["share_of_tagged_pct"] = (100 * tags["companies"] / (df["n_n_tags"] > 0).sum()).round(2)
    summary = {
        "companies_selected": n,
        "unique_industries_top_level": int(df["n_industry_top"].nunique()),
        "unique_subindustry_strings": int(df["n_subindustry_full"].nunique()),
        "unique_subindustry_children": int(df["n_subindustry_child"].nunique()),
        "unique_industries_array_values": int(inds_long["industry"].nunique()),
        "unique_tags": int(tags_long["tag"].nunique()),
        "companies_missing_industry": int(df["n_industry_top"].isna().sum()),
        "companies_industry_unspecified": int((df["n_industry_top"] == "Unspecified").sum()),
        "companies_missing_subindustry": int(df["n_subindustry_full"].isna().sum()),
        "companies_without_subindustry_child": int(df["n_subindustry_child"].isna().sum()),
        "companies_zero_tags": int((df["n_n_tags"] == 0).sum()),
        "companies_multiple_industries_array": int((df["n_n_industries"] > 1).sum()),
        "companies_multiple_tags": int((df["n_n_tags"] > 1).sum()),
        "companies_missing_regions": int(df["regions"].map(len).eq(0).sum()),
        "companies_missing_locations": int(df["all_locations"].fillna("").str.strip().eq("").sum()),
        "companies_missing_long_description": int((~df["n_has_description"]).sum()),
        "companies_missing_team_size": int(df["team_size"].isna().sum()),
        "unique_regions_values": int(pd.Series([x for v in df["regions"] for x in v]).nunique()),
        "unique_status_values": sorted(df["n_status_norm"].dropna().unique().tolist()),
        "unique_stage_values": sorted(df["stage"].dropna().unique().tolist()),
    }
    return industries, subs, inds_arr, tags, summary

def cross_check(all_records: list[dict], df_all: pd.DataFrame) -> pd.DataFrame:
    """Compare our counts over the FULL directory with meta.json and the per-list files shipped by yc-oss/api."""
    src = RAW / "yc-oss-api"
    meta = json.load(open(src / "meta.json"))
    rows = []
    def add(kind, name, ours, theirs, path):
        rows.append({"kind": kind, "label": name, "our_count": ours, "source_count": theirs, "match": ours == theirs, "source_file": path})
    for b in meta.get("batches", {}).values():
        path = b["api"].split("/api/")[-1]
        try: theirs = len(json.load(open(src / path)))
        except Exception: theirs = None
        add("batch", b["name"], int((df_all["batch"] == b["name"]).sum()), theirs, path)
        rows[-1]["meta_count"] = b.get("count")
    inds = pd.Series([x for r in all_records for x in (r.get("industries") or [])]).value_counts()
    for i in meta.get("industries", {}).values():
        path = i["api"].split("/api/")[-1]
        try: theirs = len(json.load(open(src / path)))
        except Exception: theirs = None
        add("industry(array)", i["name"], int(inds.get(i["name"], 0)), theirs, path)
        rows[-1]["meta_count"] = i.get("count")
    tags = pd.Series([x for r in all_records for x in (r.get("tags") or [])]).value_counts()
    for t in meta.get("tags", {}).values():
        path = t["api"].split("/api/")[-1]
        try: theirs = len(json.load(open(src / path)))
        except Exception: theirs = None
        add("tag", t["name"], int(tags.get(t["name"], 0)), theirs, path)
        rows[-1]["meta_count"] = t.get("count")
    add("total", "all companies", len(all_records), meta.get("companies", {}).get("all", {}).get("count") if isinstance(meta.get("companies"), dict) else None, "meta.json")
    return pd.DataFrame(rows)
