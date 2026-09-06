"""Taxonomy change detection using historical snapshots of companies/all.json (yc-oss/api git history).
Outputs: vocabulary presence/counts per snapshot, per-company relabel events, retroactive relabel rates by batch,
near-duplicate label list. No merging is performed; this only flags risks."""
from __future__ import annotations
import json, re
import pandas as pd
from .config import RAW

def _snapshots():
    return [(f.name.split("_")[1], f) for f in sorted((RAW / "snapshots").glob("all_*.json"))]

def _labels(rec):
    return {"tag": set(rec.get("tags") or []), "industry": {rec.get("industry")} - {None, ""},
            "subindustry": {rec.get("subindustry")} - {None, ""}, "industries_array": set(rec.get("industries") or [])}

def run(df_selected: pd.DataFrame, cfg: dict):
    snaps = _snapshots()
    if not snaps:
        return {}
    vocab_rows, company_state, sizes, relabel_rows = [], {}, {}, []
    prev = None
    for date, path in snaps:
        recs = json.load(open(path))
        sizes[date] = len(recs)
        counts = {"tag": {}, "industry": {}, "subindustry": {}, "industries_array": {}}
        state = {}
        for r in recs:
            labs = _labels(r)
            state[r["id"]] = (labs, r.get("batch"))
            for kind, ss in labs.items():
                for l in ss: counts[kind][l] = counts[kind].get(l, 0) + 1
        for kind, c in counts.items():
            for l, n in c.items(): vocab_rows.append({"label_type": kind, "label": l, "snapshot": date, "count": n})
        if prev is not None:
            pdate, pstate = prev
            for cid, (labs, batch) in state.items():
                if cid not in pstate: continue
                plabs = pstate[cid][0]
                for kind in ("tag", "industry", "subindustry"):
                    added, removed = labs[kind] - plabs[kind], plabs[kind] - labs[kind]
                    if added or removed:
                        relabel_rows.append({"company_id": cid, "batch": batch, "label_type": kind, "from_snapshot": pdate, "to_snapshot": date,
                                             "added": "|".join(sorted(added)), "removed": "|".join(sorted(removed))})
        prev = (date, state); company_state[date] = state
    vocab = pd.DataFrame(vocab_rows)
    wide = vocab.pivot_table(index=["label_type", "label"], columns="snapshot", values="count", fill_value=0).reset_index()
    snap_cols = [c for c in wide.columns if c not in ("label_type", "label")]
    present = wide[snap_cols] > 0
    wide["first_seen_snapshot"] = present.idxmax(axis=1)
    wide["last_seen_snapshot"] = present.iloc[:, ::-1].idxmax(axis=1)
    wide["introduced_after_first_snapshot"] = wide["first_seen_snapshot"] != snap_cols[0]
    wide["absent_in_latest_snapshot"] = ~present[snap_cols[-1]]
    wide["count_first"] = wide[snap_cols[0]]; wide["count_latest"] = wide[snap_cols[-1]]
    wide["count_change"] = wide["count_latest"] - wide["count_first"]
    wide["count_change_pct"] = (100 * wide["count_change"] / wide["count_first"].where(wide["count_first"] > 0)).round(1)
    relabels = pd.DataFrame(relabel_rows)
    first_state, last_state = company_state[snaps[0][0]], company_state[snaps[-1][0]]
    rows = []
    for b, g in df_selected.groupby("batch", sort=False):
        ids = [i for i in g["id"] if i in first_state and i in last_state]
        n = len(ids)
        def changed(kind): return sum(1 for i in ids if first_state[i][0][kind] != last_state[i][0][kind])
        AI = {"AI", "Artificial Intelligence"}
        def changed_ex_ai(): return sum(1 for i in ids if (first_state[i][0]["tag"] - AI) != (last_state[i][0]["tag"] - AI))
        ok = n >= 20  # rates on fewer than 20 overlapping companies are not reported
        rows.append({"batch": b, "batch_order": int(g["n_batch_order"].iloc[0]), "companies_in_batch": len(g), "companies_in_both_snapshots": n,
                     "first_snapshot": snaps[0][0], "latest_snapshot": snaps[-1][0],
                     "tags_changed": changed("tag"), "tags_changed_pct": round(100 * changed("tag") / n, 1) if ok else None,
                     "tags_changed_excluding_AI_ArtificialIntelligence_swaps": changed_ex_ai(),
                     "tags_changed_excluding_AI_swaps_pct": round(100 * changed_ex_ai() / n, 1) if ok else None,
                     "industry_changed": changed("industry"), "industry_changed_pct": round(100 * changed("industry") / n, 1) if ok else None,
                     "subindustry_changed": changed("subindustry"), "subindustry_changed_pct": round(100 * changed("subindustry") / n, 1) if ok else None})
    retro = pd.DataFrame(rows).sort_values("batch_order")
    flows = pd.DataFrame(columns=["removed_label", "added_label", "companies"])
    if not relabels.empty:
        t = relabels[relabels.label_type == "tag"]
        pairs = [(r, a) for rem, add in zip(t["removed"], t["added"]) for r in rem.split("|") if r for a in add.split("|") if a]
        if pairs:
            vc = pd.Series(pairs).value_counts().head(300)
            flows = pd.DataFrame([{"removed_label": a, "added_label": b, "companies": int(n)} for (a, b), n in vc.items()])
    tags = sorted(set(vocab[vocab.label_type == "tag"]["label"]))
    def stem(s):
        s = re.sub(r"[^a-z0-9]", "", s.lower()); return s[:-1] if s.endswith("s") else s
    dup, by = [], {}
    for t_ in tags: by.setdefault(stem(t_), []).append(t_)
    for k, v in by.items():
        if len(v) > 1: dup.append({"rule": "same after lowercasing/punctuation/plural", "labels": " | ".join(v)})
    synonyms = [("AI", "Artificial Intelligence"), ("Biotech", "Biotechnology"), ("Climate", "ClimateTech"), ("Cultivated Meat", "Cultured Meat"),
                ("Cultivated Meat", "Clean Meat"), ("Crypto / Web3", "Cryptocurrency"), ("Crypto / Web3", "Crypto"), ("Chatbot", "Chatbots"),
                ("API", "APIs"), ("Machine Learning", "ML"), ("E-commerce", "eCommerce"), ("Generative AI", "GenAI"),
                ("SaaS", "Enterprise Software"), ("Health Tech", "Healthcare"), ("Edtech", "Education"), ("Fintech", "Financial Services"),
                ("Insurtech", "Insurance"), ("Proptech", "Real Estate"), ("Conversational AI", "Chatbot"), ("AI Assistant", "AI")]
    tagset = set(tags)
    for a, b in synonyms:
        if a in tagset and b in tagset: dup.append({"rule": "overlapping meaning by name (listed, not merged)", "labels": f"{a} | {b}"})
    near = pd.DataFrame(dup).drop_duplicates()
    summary = {"n_snapshots": len(snaps), "first_snapshot": snaps[0][0], "latest_snapshot": snaps[-1][0], "companies_per_snapshot": sizes,
               "tags_introduced_after_first_snapshot": int(((wide.label_type == "tag") & wide.introduced_after_first_snapshot).sum()),
               "tags_absent_in_latest": int(((wide.label_type == "tag") & wide.absent_in_latest_snapshot).sum()),
               "subindustries_introduced_after_first_snapshot": int(((wide.label_type == "subindustry") & wide.introduced_after_first_snapshot).sum()),
               "relabel_events": int(len(relabels))}
    return {"vocab": wide.sort_values(["label_type", "label"]), "relabels": relabels, "retro": retro, "flows": flows, "near_duplicates": near, "summary": summary}
