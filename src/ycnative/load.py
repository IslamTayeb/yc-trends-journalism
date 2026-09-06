"""Load yc-oss/api companies/all.json into a one-row-per-company DataFrame, preserving raw fields.
Derived fields are prefixed n_ ; raw YC labels are never overwritten."""
from __future__ import annotations
import json, re
import pandas as pd
from .config import RAW

RAW_FIELDS = ["id","name","slug","former_names","website","url","batch","one_liner","long_description",
              "team_size","all_locations","industry","subindustry","industries","tags","tags_highlighted",
              "regions","stage","status","isHiring","nonprofit","top_company","launched_at",
              "app_video_public","demo_day_video_public","question_answers","small_logo_thumb_url","api"]
LIST_FIELDS = ["former_names","industries","tags","tags_highlighted","regions"]
SEASON_RANK = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}
SEASON_CODE = {"Winter": "W", "Spring": "X", "Summer": "S", "Fall": "F"}  # YC uses X for Spring
REMOTE_FLAGS = {"Remote", "Fully Remote", "Partly Remote"}
# Region strings that are not countries (enumerated from data; anything else in `regions` is treated as a country)
MACRO_REGIONS = {"America / Canada","Europe","Latin America","South Asia","Southeast Asia","East Asia","Middle East and North Africa","Middle East / North Africa",
                 "Africa","Oceania","Asia","North America","Sub-Saharan Africa","Central Asia","Caribbean","Unspecified"}

def read_all() -> list[dict]:
    return json.load(open(RAW / "yc-oss-api" / "companies" / "all.json"))

def parse_batch(b: str):
    m = re.fullmatch(r"(Winter|Spring|Summer|Fall)\s+(\d{4})", (b or "").strip())
    if not m:
        return None, None, None, None
    season, year = m.group(1), int(m.group(2))
    return season, year, f"{SEASON_CODE[season]}{str(year)[2:]}", year * 10 + SEASON_RANK[season]

def to_frame(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        row = {k: r.get(k) for k in RAW_FIELDS}
        for k in LIST_FIELDS:
            row[k] = list(r.get(k) or [])
        season, year, code, order = parse_batch(r.get("batch"))
        row["n_batch_season"] = season
        row["n_year"] = year
        row["n_batch_code"] = code
        row["n_batch_order"] = order
        row["n_batch_valid"] = season is not None
        sub = (r.get("subindustry") or "").strip()
        parts = [p.strip() for p in sub.split("->")] if sub else []
        row["n_industry_top"] = (r.get("industry") or "").strip() or None
        row["n_subindustry_full"] = sub or None
        row["n_subindustry_child"] = parts[1] if len(parts) > 1 else None
        row["n_tags_norm"] = [re.sub(r"\s+", " ", t).strip() for t in (r.get("tags") or []) if t and t.strip()]
        row["n_n_tags"] = len(row["n_tags_norm"])
        row["n_n_industries"] = len(row["industries"])
        regs = set(row["regions"])
        row["n_is_us"] = "United States of America" in regs
        row["n_is_remote"] = bool(regs & REMOTE_FLAGS)
        row["n_remote_kind"] = next((x for x in ("Fully Remote","Partly Remote") if x in regs), "Remote" if "Remote" in regs else None)
        row["n_countries"] = [x for x in row["regions"] if x not in REMOTE_FLAGS and x not in MACRO_REGIONS]
        row["n_macro_regions"] = [x for x in row["regions"] if x in MACRO_REGIONS]
        loc = (r.get("all_locations") or "").strip()
        segs = [s.strip() for s in loc.split(";") if s.strip()]
        first = next((s for s in segs if s.lower() != "remote"), None)
        if first:
            toks = [t.strip() for t in first.split(",")]
            row["n_city"] = toks[0] if toks else None
            row["n_country_from_locations"] = toks[-1] if len(toks) > 1 else None
        else:
            row["n_city"] = None; row["n_country_from_locations"] = None
        row["n_status_norm"] = (r.get("status") or "").strip() or None
        row["n_has_description"] = bool((r.get("long_description") or "").strip())
        row["n_launched_date"] = pd.to_datetime(r.get("launched_at"), unit="s", errors="coerce") if r.get("launched_at") else pd.NaT
        rows.append(row)
    df = pd.DataFrame(rows)
    df["yc_profile_url"] = df["url"]
    return df

def select_window(df: pd.DataFrame, start_year: int, end_year: int | None, min_full_batch: int):
    """Return (analysis df, excluded df). Adds n_batch_is_partial."""
    valid = df["n_batch_valid"] & (df["n_year"] >= start_year)
    if end_year is not None:
        valid &= df["n_year"] <= end_year
    sel = df[valid].copy()
    sizes = sel.groupby("batch")["id"].size()
    sel["n_batch_size"] = sel["batch"].map(sizes)
    sel["n_batch_is_partial"] = sel["n_batch_size"] < min_full_batch
    return sel.sort_values(["n_batch_order", "name"]).reset_index(drop=True), df[~valid].copy()

def batch_order(df: pd.DataFrame) -> list[str]:
    return list(df.drop_duplicates("batch").sort_values("n_batch_order")["batch"])

def list_to_str(v):
    return "|".join(v) if isinstance(v, list) else v

def long_tables(df: pd.DataFrame):
    base = df[["id","slug","batch","n_batch_code","n_year"]].rename(columns={"id":"company_id","slug":"company_slug","n_batch_code":"batch_code","n_year":"year"})
    tags = base.join(df["n_tags_norm"].rename("tag")).explode("tag").dropna(subset=["tag"])
    inds = base.join(df["industries"].rename("industry")).explode("industry").dropna(subset=["industry"])
    inds["level"] = ["top" if i == t else "child" for i, t in zip(inds["industry"], df.loc[inds.index, "n_industry_top"])]
    subs = base.join(df[["n_subindustry_full","n_industry_top","n_subindustry_child"]].rename(
        columns={"n_subindustry_full":"subindustry","n_industry_top":"industry","n_subindustry_child":"subindustry_child"})).dropna(subset=["subindustry"])
    return tags.reset_index(drop=True), inds.reset_index(drop=True), subs.reset_index(drop=True)

def companies_csv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in LIST_FIELDS + ["n_tags_norm","n_countries","n_macro_regions"]:
        out[c] = out[c].map(list_to_str)
    return out
