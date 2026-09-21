"""Merge the per-chunk labels, validate them against the company table, and aggregate per batch.

    uv run python fullstack/collect.py     # fullstack/data/yc_fullstack_labels.csv, yc_fullstack_by_batch.csv; prints headline numbers

Aborts if any classified company is missing, duplicated, unknown, or carries a category outside the rubric.
"""
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FS = ROOT / "fullstack"
CATS = ["full_stack_ai", "sells_ai_to_industry", "ai_infra", "ai_other", "full_stack_non_ai", "not_ai", "unclear"]
AI_CATS = ["full_stack_ai", "sells_ai_to_industry", "ai_infra", "ai_other"]
START_ORDER = 20190

chunks = sorted((FS / "work/chunks").glob("chunk_*.jsonl"))
labels, problems = [], []
for c in chunks:
    ids = [json.loads(l)["id"] for l in c.read_text().split("\n") if l.strip()]
    lp = FS / "work/labels" / c.name
    if not lp.exists(): problems.append(f"{lp.name}: missing"); continue
    rows = []
    for i, l in enumerate(lp.read_text().split("\n")):
        if not l.strip(): continue
        try: rows.append(json.loads(l))
        except json.JSONDecodeError as e: problems.append(f"{lp.name}:{i + 1}: bad JSON ({e})")
    got = [r.get("id") for r in rows]
    if sorted(got) != sorted(ids):
        problems.append(f"{lp.name}: ids differ from input (missing {sorted(set(ids) - set(got))[:5]}, extra {sorted(set(got) - set(ids))[:5]}, "
                        f"{len(got)} vs {len(ids)} lines)")
    for r in rows:
        if r.get("category") not in CATS: problems.append(f"{lp.name}: id {r.get('id')} category {r.get('category')!r}")
        if r.get("confidence") not in ("high", "medium", "low"): problems.append(f"{lp.name}: id {r.get('id')} confidence {r.get('confidence')!r}")
        r["chunk"] = c.stem
    labels += rows
if problems:
    print("\n".join(problems[:40])); print(f"{len(problems)} problems"); sys.exit(1)

lab = pd.DataFrame(labels)[["id", "category", "confidence", "reason", "chunk"]]
# second pass: every first-pass full_stack_ai was re-read by one reviewer against the rubric; flips live in review_overrides.csv
ov = pd.read_csv(FS / "review_overrides.csv")
assert ov.id.is_unique and ov.category.isin(CATS).all() and set(ov.id) <= set(lab.id), "bad override"
lab["category_first_pass"] = lab.category
lab = lab.merge(ov.rename(columns={"category": "cat_ov", "confidence": "conf_ov", "note": "review_note"}), on="id", how="left")
flip = lab.cat_ov.notna()
lab.loc[flip, "category"], lab.loc[flip, "confidence"] = lab.cat_ov[flip], lab.conf_ov[flip]
lab["reviewed"] = lab.category_first_pass == "full_stack_ai"
lab = lab.drop(columns=["cat_ov", "conf_ov"])
print(f"review: {lab.reviewed.sum()} first-pass full_stack_ai read again, {flip.sum()} moved: {lab[flip].category.value_counts().to_dict()}")
d = pd.read_csv(ROOT / "data/all_years/processed/yc_companies_native.csv")
d = d[d.n_batch_order >= START_ORDER]
assert set(lab.id) == set(d.id) and lab.id.is_unique, "label ids do not match the company table"
out = d[["id", "name", "batch", "n_batch_code", "n_batch_order", "one_liner", "industry", "subindustry", "tags", "yc_profile_url",
         "n_batch_size", "n_batch_is_partial"]].merge(lab, on="id")
out["reviewed"] = out.reviewed.fillna(False)
out["full_stack_ai"] = out.category == "full_stack_ai"
out["caption"] = out.category.map({"full_stack_ai": "full-stack AI startup", "full_stack_non_ai": "full-stack startup, not AI-run",
                                    "sells_ai_to_industry": "sells AI to the industry", "ai_infra": "AI infrastructure",
                                    "ai_other": "other AI", "not_ai": "not AI", "unclear": "unclear"})
out = out.rename(columns={"n_batch_code": "batch_code", "n_batch_order": "batch_order", "n_batch_size": "batch_size",
                          "n_batch_is_partial": "is_partial_batch"}).sort_values(["batch_order", "name"])
(FS / "data").mkdir(exist_ok=True)
out.to_csv(FS / "data/yc_fullstack_labels.csv", index=False)

# per batch: count per category, share of batch, share of AI companies
g = out.groupby(["batch_order", "batch_code", "batch", "is_partial_batch"])
b = g.size().rename("total_companies").to_frame()
for c in CATS: b[f"n_{c}"] = g.apply(lambda x, c=c: (x.category == c).sum())
b["n_ai_any"] = b[[f"n_{c}" for c in AI_CATS]].sum(axis=1)
for c in ("full_stack_ai", "full_stack_non_ai", "sells_ai_to_industry"):
    b[f"{c}_share_pct"] = (100 * b[f"n_{c}"] / b.total_companies).round(2)
b["ai_any_share_pct"] = (100 * b.n_ai_any / b.total_companies).round(2)
b["full_stack_ai_share_of_ai_pct"] = (100 * b.n_full_stack_ai / b.n_ai_any.where(b.n_ai_any > 0)).round(2)
b["n_full_stack_ai_high_conf"] = g.apply(lambda x: ((x.category == "full_stack_ai") & (x.confidence == "high")).sum())
b = b.reset_index()
b["start_month"] = b.batch.map(lambda s: f"{s.split()[1]}-{ {'Winter': 1, 'Spring': 4, 'Summer': 6, 'Fall': 9}[s.split()[0]]:02d}")
b.to_csv(FS / "data/yc_fullstack_by_batch.csv", index=False)

print(f"{len(out)} companies, {out.batch.iloc[0]} to {out.batch.iloc[-1]}")
print(out.category.value_counts().to_string())
print("confidence among full_stack_ai:", out[out.full_stack_ai].confidence.value_counts().to_dict())
full = b[~b.is_partial_batch]
cols = ["batch_code", "total_companies", "n_full_stack_ai", "full_stack_ai_share_pct", "n_full_stack_non_ai", "full_stack_non_ai_share_pct",
        "sells_ai_to_industry_share_pct", "ai_any_share_pct", "full_stack_ai_share_of_ai_pct"]
print(full[cols].to_string(index=False))
