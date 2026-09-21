"""Write the companies to classify as JSONL chunks for the rubric in rubric.md.

    uv run python fullstack/prepare_chunks.py            # fullstack/work/chunks/chunk_NN.jsonl, ~150 companies each
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "fullstack/work"
START_ORDER, CHUNK, MAX_DESC = 20190, 150, 1500      # Winter 2019 onward, like the blog figures

d = pd.read_csv(ROOT / "data/all_years/processed/yc_companies_native.csv")
d = d[d.n_batch_order >= START_ORDER].sort_values(["n_batch_order", "name"]).reset_index(drop=True)
rows = []
for r in d.itertuples():
    desc = "" if pd.isna(r.long_description) else str(r.long_description).strip()
    if len(desc) > MAX_DESC: desc = desc[:MAX_DESC].rsplit(" ", 1)[0] + " …"
    rows.append({"id": int(r.id), "name": r.name, "batch": r.batch,
                 "one_liner": "" if pd.isna(r.one_liner) else str(r.one_liner).strip(),
                 "industry": "" if pd.isna(r.industry) else r.industry,
                 "subindustry": "" if pd.isna(r.subindustry) else r.subindustry,
                 "tags": "" if pd.isna(r.tags) else r.tags, "description": desc})
out = WORK / "chunks"; out.mkdir(parents=True, exist_ok=True)
for p in out.glob("chunk_*.jsonl"): p.unlink()
for i in range(0, len(rows), CHUNK):
    (out / f"chunk_{i // CHUNK:02d}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[i:i + CHUNK]))
print(len(rows), "companies,", (len(rows) + CHUNK - 1) // CHUNK, "chunks,", d.batch.iloc[0], "to", d.batch.iloc[-1])
