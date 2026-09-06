"""Optional enrichment from EXTREMOPHILARUM/yc-dataset (secondary source). Adds ycds_* columns; never overrides YC labels."""
from __future__ import annotations
import json, re
import pandas as pd, yaml
from .config import RAW

def load_secondary():
    idx = pd.DataFrame(json.load(open(RAW / "yc-dataset" / "index.json"))).rename(
        columns={"batch": "ycds_batch_code", "status": "ycds_status", "has_postmortem": "ycds_has_postmortem", "name": "ycds_name"})
    d = json.load(open(RAW / "yc-dataset" / "yc_directory.json"))
    dd = pd.DataFrame([{"id": r.get("id"), "ycds_tags": "|".join(r.get("tags") or []), "ycds_industry": r.get("industry"),
                        "ycds_subindustry": r.get("subindustry"), "ycds_batch": r.get("batch"), "ycds_status_dir": r.get("status")} for r in d])
    fm_rows = []
    root = RAW / "clones" / "yc-dataset" / "data"
    if root.exists():
        for p in root.glob("*/*/company.md"):
            try:
                m = re.match(r"---\n(.*?)\n---", p.read_text(errors="ignore"), re.S)
                if not m: continue
                fm = yaml.safe_load(m.group(1)) or {}
                fm_rows.append({"slug": fm.get("slug") or p.parent.name, "ycds_year_founded": fm.get("year_founded"), "ycds_city": fm.get("city"),
                                "ycds_country": fm.get("country"), "ycds_linkedin_url": fm.get("linkedin_url"), "ycds_twitter_url": fm.get("twitter_url")})
            except Exception:
                continue
    fm = pd.DataFrame(fm_rows).drop_duplicates("slug") if fm_rows else pd.DataFrame(columns=["slug"])
    return idx, dd, fm

def enrich(df: pd.DataFrame):
    idx, dd, fm = load_secondary()
    out = df.merge(dd, on="id", how="left").merge(idx.drop(columns=["ycds_name"]), on="slug", how="left")
    if not fm.empty: out = out.merge(fm, on="slug", how="left")
    out["ycds_present"] = out["ycds_batch"].notna()
    both = out[out["ycds_present"]]
    agree = {"companies_selected": len(df), "in_secondary": int(out["ycds_present"].sum()), "coverage_pct": round(float(100 * out["ycds_present"].mean()), 2),
             "tags_identical_pct": round(float(100 * (both["ycds_tags"] == both["n_tags_norm"].map("|".join)).mean()), 2) if len(both) else None,
             "industry_identical_pct": round(float(100 * (both["ycds_industry"] == both["industry"]).mean()), 2) if len(both) else None,
             "subindustry_identical_pct": round(float(100 * (both["ycds_subindustry"] == both["subindustry"]).mean()), 2) if len(both) else None}
    cov = out.groupby("batch", sort=False)["ycds_present"].agg(["size", "sum"]).rename(columns={"size": "companies", "sum": "in_secondary"}).reset_index()
    cov["coverage_pct"] = (100 * cov["in_secondary"] / cov["companies"]).round(1)
    return out, agree, cov
