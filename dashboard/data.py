"""Read-only loaders for the pipeline outputs used by the dashboard.

Everything comes from data/all_years/processed (full 2005+ history). The dashboard
never writes under data/.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "all_years" / "processed"
PROV = ROOT / "data" / "provenance.json"
CONFIG = ROOT / "config.yaml"

TABLES = {
    "companies": "yc_companies_native.csv",
    "tags": "yc_company_tags.csv",
    "industries": "yc_company_industries.csv",
    "subindustries": "yc_company_subindustries.csv",
    "batch_summary": "yc_batch_summary.csv",
    "diversity": "yc_diversity.csv",
    "geo_trends": "yc_geography_trends.csv",
    "geo_macro": "yc_geography_macro_regions.csv",
    "geo_countries": "yc_geography_countries.csv",
    "geo_cities": "yc_geography_cities.csv",
    "rfs_requests": "yc_rfs_requests.csv",
    "rfs_editions": "yc_rfs_editions.csv",
    "rfs_mentions": "yc_rfs_label_mentions.csv",
    "relabel_by_batch": "yc_retroactive_relabeling_by_batch.csv",
    "relabel_flows": "yc_tag_relabel_flows.csv",
    "near_duplicates": "yc_near_duplicate_labels.csv",
    "taxonomy_history": "yc_taxonomy_history.csv",
}

BATCH_META_COLS = [
    "batch", "batch_code", "year", "season", "batch_order", "total_companies",
    "is_partial_batch", "low_tag_coverage", "zero_tag_companies", "zero_tag_pct",
]


@st.cache_data(show_spinner=False)
def load_table(key: str) -> pd.DataFrame:
    path = PROC / TABLES[key]
    df = pd.read_csv(path, low_memory=False)
    return df


@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    return {k: load_table(k) for k in TABLES}


@st.cache_data(show_spinner=False)
def config() -> dict:
    # Read the YAML directly: ycnative.config.load_config mkdirs output dirs as a side effect.
    with open(CONFIG) as fh:
        return yaml.safe_load(fh)


@st.cache_data(show_spinner=False)
def provenance() -> dict:
    if PROV.exists():
        return json.loads(PROV.read_text())
    return {}


@st.cache_data(show_spinner=False)
def batch_meta() -> pd.DataFrame:
    """One row per batch in chronological order with the flags every view needs."""
    bs = load_table("batch_summary")
    meta = bs[BATCH_META_COLS].copy()
    meta["is_partial_batch"] = meta["is_partial_batch"].astype(bool)
    meta["low_tag_coverage"] = meta["low_tag_coverage"].astype(bool)
    meta["tagged_companies"] = meta["total_companies"] - meta["zero_tag_companies"]
    meta = meta.sort_values("batch_order").reset_index(drop=True)
    meta["pos"] = range(len(meta))  # x position for charts
    return meta


def window_meta(meta: pd.DataFrame, start_year: int, end_year: int | None) -> pd.DataFrame:
    m = meta[meta["year"] >= start_year]
    if end_year is not None:
        m = m[m["year"] <= end_year]
    m = m.reset_index(drop=True)
    m["pos"] = range(len(m))
    return m


def attach_batch(df: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Restrict a table with a `batch` column to the window and add batch_order / pos / flags."""
    cols = ["batch", "batch_order", "pos", "is_partial_batch", "low_tag_coverage"]
    out = df.drop(columns=[c for c in cols[1:] if c in df.columns], errors="ignore")
    return out.merge(meta[cols], on="batch", how="inner")
