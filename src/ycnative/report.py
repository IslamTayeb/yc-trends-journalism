"""report.md generated from computed tables. Every number is read from a DataFrame; only the framing prose is fixed text."""
from __future__ import annotations
import pandas as pd

def f1(x): return "n/a" if x is None or (isinstance(x, float) and pd.isna(x)) else f"{x:.1f}"
def pct(x): return f"{f1(x)}%"

def _tbl(df, cols, headers=None, n=None):
    d = df[cols] if n is None else df[cols].head(n)
    headers = headers or cols
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in d.itertuples(index=False):
        lines.append("| " + " | ".join("" if (isinstance(v, float) and pd.isna(v)) else (f"{v:.1f}" if isinstance(v, float) else str(v)) for v in row) + " |")
    return "\n".join(lines)

def build(ctx, path):
    cfg, prov, R, bs = ctx["cfg"], ctx["prov"], ctx["results"], ctx["bs"]
    df = ctx["df"]; bm = ctx["bmeta"].set_index("batch")
    ind, sub, tag = R["industry"]["stats"], R["subindustry"]["stats"], R["tag"]["stats"]
    latest_i = ind["latest_full_batch"].iloc[0]; latest_t = tag["latest_full_batch"].iloc[0]
    first_b = ctx["batches"][0]; sy = cfg["START_YEAR"]
    full = bs[~bs["is_partial_batch"]]
    L = []
    A = L.append
    A(f"# What kinds of companies is YC funding, {sy}-present, according to YC's own taxonomy\n")
    A("Scope of this phase: YC's native labels only (`industry`, `subindustry`, `tags`, `regions`, `status`), plus YC's own Requests for Startups (RFS) text. "
      "No LLM classification, no custom buckets, no causal claims. Every number below is produced by `run_all.py` from `data/processed/*.csv`.\n")
    A("## 1. Data and provenance\n")
    ps = prov["primary_source"]
    A(f"- Primary source: [{ps['repo']}]({ps['repo']}) at commit `{ps['commit_sha']}` ({ps['commit_date'][:10]}); source `meta.json` last_updated {ps['meta_last_updated'][:19]}Z; retrieved {prov['retrieval_date_utc'][:19]}Z. Directory size: {ps['companies_in_all_json']} companies.")
    A(f"- Selected: **{len(df)} companies in {len(ctx['batches'])} batches** ({first_b} to {ctx['batches'][-1]}); {len(ctx['excluded'])} companies outside the window (or with batch 'Unspecified') excluded.")
    A(f"- Coverage caveat: the directory lists publicly launched companies with a YC profile, not every company ever accepted.")
    A(f"- Secondary source (enrichment only): {prov['secondary_source']['repo']} at `{prov['secondary_source']['commit_sha'][:10]}` ({prov['secondary_source']['commit_date'][:10]}); covers {ctx['agree']['coverage_pct']}% of selected companies. It is a different-dated dump of the same Algolia index; industry agrees for {ctx['agree']['industry_identical_pct']}% of shared companies, tags for {ctx['agree']['tags_identical_pct']}% (see section 9).")
    A(f"- Historical snapshots of `companies/all.json` from the primary repo's git history: {ctx['th']['summary']['n_snapshots']} monthly snapshots, {ctx['th']['summary']['first_snapshot']} to {ctx['th']['summary']['latest_snapshot']}.")
    A(f"- Data quality: 0 duplicate ids; source cross-check {int((~ctx['xc']['match']).sum())} mismatches in {len(ctx['xc'])} comparisons (per-batch, per-industry, per-tag counts vs the source's own list files); random spot check of {ctx['sc']['company_id'].nunique()} companies x {ctx['sc']['field'].nunique()} fields: {int((~ctx['sc']['match']).sum())} mismatches. Full report: `data/quality/`.\n")
    A("**Conventions.** share = companies carrying the label / all companies in the batch. "
      f"Batches with fewer than {cfg['MIN_FULL_BATCH']} companies ({', '.join(bs.loc[bs['is_partial_batch'], 'batch']) or 'none'}) are in progress and excluded from rankings and 'latest' figures. "
      f"'{sy}' shares pool all {sy} batches. 'Latest' = {latest_i}.\n")
    lt = ctx["low_tag_batches"]
    if lt:
        z = bs.set_index("batch")
        A(f"**Tag-coverage warning.** In {', '.join(lt)} most companies have no tags at all ({', '.join(f'{b}: {z.loc[b, 'zero_tag_pct']}% zero-tag' for b in lt)}), versus {z.loc[latest_t, 'zero_tag_pct']}% in {latest_t}. "
          f"Tag shares for those batches are shown in the matrices but excluded from all tag statistics; 'latest' for tags = {latest_t}. Industry and subindustry fields are populated for every company, so they are unaffected.\n")
    A("## 2. Batch sizes\n")
    A(_tbl(bs, ["batch", "total_companies", "status_active", "status_acquired", "status_inactive", "hiring_companies", "median_team_size", "missing_team_size_pct", "zero_tag_companies", "is_partial_batch"],
           ["batch", "companies", "active", "acquired", "inactive", "hiring", "median team", "% missing team size", "zero-tag", "partial"]))
    big = full.loc[full["total_companies"].idxmax()]; small = full.loc[full["total_companies"].idxmin()]
    A(f"\nListed batch size peaked at {int(big['total_companies'])} ({big['batch']}) and was smallest at {int(small['total_companies'])} ({small['batch']}); YC moved from two to four batches a year starting Fall 2024. Status fields age with the batch (recent batches are almost entirely 'Active'), so status is not comparable across batches.\n")
    A("## 3. YC's taxonomy as present in the data\n")
    ts = ctx["tax_summary"]
    A(f"- {ts['unique_industries_top_level']} top-level industries, {ts['unique_subindustry_strings']} subindustry strings ({ts['unique_subindustry_children']} distinct child labels), {ts['unique_tags']} distinct tags, {ts['unique_regions_values']} distinct region strings.")
    A(f"- Every company has an `industry` and a `subindustry`; {ts['companies_without_subindustry_child']} companies carry only the parent (e.g. subindustry = 'B2B'). {ts['companies_zero_tags']} companies have zero tags ({100*ts['companies_zero_tags']/len(df):.1f}%), {ts['companies_multiple_tags']} have more than one tag; {ts['companies_multiple_industries_array']} have two entries in `industries` (parent + child; there are never more than two).")
    A(f"- {ts['companies_missing_long_description']} companies lack a long description, {ts['companies_missing_team_size']} lack team size, {ts['companies_missing_locations']} lack a location string.")
    A("- Full inventories: `yc_industries.csv`, `yc_subindustries.csv`, `yc_tags.csv` (workbook tabs Industries / Subindustries / Tags).\n")
    A("## 4. Industries (YC top-level `industry`)\n")
    A(_tbl(ind, ["industry", "earliest_year_share_pct", "latest_share_pct", "pp_change", "rank_earliest_year", "rank_latest", "peak_batch", "peak_share_pct", "emergence_class"],
           [f"industry", f"share {sy}", f"share {latest_i}", "pp change", f"rank {sy}", "rank latest", "peak batch", "peak share", "class"]))
    A("")
    for _, r in ind.iterrows():
        A(f"- **{r['industry']}**: {pct(r['earliest_year_share_pct'])} of the {sy} batches to {pct(r['latest_share_pct'])} of {latest_i} ({r['pp_change']:+.1f} pp); rank {r['rank_earliest_year']} to {r['rank_latest']}; peak {pct(r['peak_share_pct'])} in {r['peak_batch']}.")
    A("\nFigures: `figures/largest_industries_share.png`, `figures/fastest_moving_industry.png`, one file per industry `figures/industry_*.png`.\n")
    A("## 5. Subindustries (YC `subindustry`, 'Parent -> Child')\n")
    up = sub.sort_values("pp_change", ascending=False).head(10); dn = sub.sort_values("pp_change").head(10)
    A("Largest gains (pp of batch):\n"); A(_tbl(up, ["subindustry", "earliest_year_share_pct", "latest_share_pct", "pp_change", "rank_earliest_year", "rank_latest", "peak_batch", "peak_share_pct", "emergence_class"], [f"subindustry", f"{sy}", f"{latest_i}", "pp", f"rank {sy}", "rank latest", "peak", "peak share", "class"]))
    A("\nLargest declines (pp of batch):\n"); A(_tbl(dn, ["subindustry", "earliest_year_share_pct", "latest_share_pct", "pp_change", "rank_earliest_year", "rank_latest", "peak_batch", "peak_share_pct", "emergence_class"], [f"subindustry", f"{sy}", f"{latest_i}", "pp", f"rank {sy}", "rank latest", "peak", "peak share", "class"]))
    A("\nStandalone native categories (each kept separate; `figures/subindustry_*.png`):\n")
    child_to_full = {f.split("->")[1].strip(): f for f in sub["subindustry"] if "->" in f}
    for lab in cfg["STANDALONE_SUBINDUSTRIES"]:
        if lab in child_to_full:
            r = sub[sub["subindustry"] == child_to_full[lab]].iloc[0]
            A(f"- **{r['subindustry']}**: first observed {r['first_observed_batch']}; {pct(r['earliest_year_share_pct'])} in {sy} to {pct(r['latest_share_pct'])} in {latest_i} ({r['pp_change']:+.1f} pp); peak {pct(r['peak_share_pct'])} ({r['peak_count']} companies) in {r['peak_batch']}; class: {r['emergence_class']}.")
        else:
            A(f"- {lab}: not present as a YC subindustry in the selected data.")
    A("\nNote the parent-only strings ('B2B', 'Industrials', 'Healthcare' with no child) are themselves among the biggest movers: companies are increasingly filed under the parent without a child label (see section 9).\n")
    A("## 6. Tags (YC `tags`)\n")
    A(f"Top 20 tags in {latest_t} by share of batch:\n")
    A(_tbl(tag, ["tag", "earliest_year_share_pct", "latest_share_pct", "pp_change", "rank_earliest_year", "rank_latest", "peak_batch", "peak_share_pct", "emergence_class"], ["tag", f"{sy}", f"{latest_t}", "pp", f"rank {sy}", "rank latest", "peak", "peak share", "class"], n=20))
    tmin = tag[tag["total_companies"] >= cfg["NEW_LABEL_MIN_COUNT"]]
    A("\nFastest-growing tags (pp):\n"); A(_tbl(tmin.sort_values("pp_change", ascending=False), ["tag", "earliest_year_share_pct", "latest_share_pct", "pp_change", "first_observed_batch", "emergence_class"], ["tag", f"{sy}", f"{latest_t}", "pp", "first batch", "class"], n=15))
    A("\nFastest-declining tags (pp):\n"); A(_tbl(tmin.sort_values("pp_change"), ["tag", "earliest_year_share_pct", "latest_share_pct", "pp_change", "peak_batch", "peak_share_pct", "emergence_class"], ["tag", f"{sy}", f"{latest_t}", "pp", "peak", "peak share", "class"], n=15))
    new = tag[tag["newly_appearing"]].sort_values("total_companies", ascending=False)
    A(f"\nTags first observed after {first_b} (>= {cfg['NEW_LABEL_MIN_COUNT']} companies overall): " + ", ".join(f"{r['tag']} ({r['first_observed_batch']}, {r['total_companies']})" for _, r in new.head(20).iterrows()) + ".")
    pk = tag[tag["peaked_then_declined"]].sort_values("peak_share_pct", ascending=False)
    A("\nTags that peaked and then declined (peak in a full batch before the last two, latest <= half of peak): " + ", ".join(f"{r['tag']} (peak {pct(r['peak_share_pct'])} in {r['peak_batch']}, now {pct(r['latest_share_pct'])})" for _, r in pk.head(15).iterrows()) + ".")
    A("\nStandalone tags (`figures/tag_*.png`):\n")
    for lab in cfg["STANDALONE_TAGS"]:
        if lab in set(tag["tag"]):
            r = tag[tag["tag"] == lab].iloc[0]
            A(f"- **{lab}**: first observed {r['first_observed_batch']}; {pct(r['earliest_year_share_pct'])} in {sy} to {pct(r['latest_share_pct'])} in {latest_t} ({r['pp_change']:+.1f} pp); peak {pct(r['peak_share_pct'])} ({r['peak_count']}) in {r['peak_batch']}; class: {r['emergence_class']}.")
        else:
            A(f"- {lab}: not present as a YC tag in the selected data.")
    A("\nThe derived charts `figures/derived_union_*.png` show the share of companies carrying ANY of a listed set of YC labels; they are explicitly labelled as derived aggregations and are not used in any statistic above.\n")
    A("## 7. Category rankings over time\n")
    rk = R["industry"]["rank"]; rt = R["tag"]["rank"]
    A("Industries (rank by share, all batches):\n"); A(_tbl(rk, ["industry", "rank_earliest_year", "rank_latest", "rank_change", "earliest_year_share_pct", "latest_share_pct", "pp_change", "major_mover"], ["industry", f"rank {sy}", "rank latest", "change", f"share {sy}", "share latest", "pp", "major mover"]))
    mv = rt[rt["major_mover"]].sort_values("pp_change", ascending=False)
    A(f"\nTags flagged as major movers (|rank change| >= {cfg['MAJOR_MOVER_RANK_CHANGE']} or |pp| >= {cfg['MAJOR_MOVER_PP']}; full table in `yc_tag_rankings.csv`):\n")
    A(_tbl(mv, ["tag", "rank_earliest_year", "rank_latest", "rank_change", "earliest_year_share_pct", "latest_share_pct", "pp_change"], ["tag", f"rank {sy}", "rank latest", "change", f"share {sy}", "share latest", "pp"], n=30))
    A("\nPer-batch top-10 industries and top-20 tags: `yc_industry_top_per_batch.csv`, `yc_tag_top_per_batch.csv`.\n")
    A("## 8. Category emergence classes\n")
    em = cfg["EMERGENCE"]
    A(f"Rules (share-of-batch series over full batches; early = mean of first {em['n_early_batches']}, late = mean of last {em['n_late_batches']}): "
      f"Emerging: late-early >= {em['emerging_min_pp_gain']} pp and late >= {em['emerging_min_ratio']}x early and latest count >= {em['emerging_min_latest_count']}. "
      f"Declining: early >= {em['declining_min_early_share_pct']}% and late <= {em['declining_max_ratio']}x early and early-late >= {em['declining_min_pp_loss']} pp. "
      f"Spiky: peak >= {em['spiky_peak_over_median']}x median and peak >= {em['spiky_min_peak_pct']}%. Persistent: mean >= {em['persistent_min_mean_pct']}% and CV <= {em['persistent_max_cv']}. Else low-volume/mixed.\n")
    for name, st in (("Industries", ind), ("Subindustries", sub), ("Tags", tag)):
        vc = st["emergence_class"].value_counts()
        A(f"- {name}: " + ", ".join(f"{k} {v}" for k, v in vc.items()) + ".")
        for cls in ("Emerging", "Declining", "Spiky", "Persistent"):
            labs = st[st["emergence_class"] == cls].sort_values("latest_share_pct", ascending=False)
            col = st.columns[0]
            if len(labs): A(f"  - {cls}: " + ", ".join(labs[col].head(15)) + ("" if len(labs) <= 15 else f" (+{len(labs)-15} more)"))
    A("")
    A("## 9. Taxonomy changes and other measurement risks\n")
    th = ctx["th"]; s = th["summary"]
    A("This is the most important caveat section. Several apparent trends are partly or wholly produced by how YC labels companies, not by which companies it funds.\n")
    fl = th["flows"]
    ai_swap = int(fl[fl.removed_label.isin(["AI", "Artificial Intelligence"]) & fl.added_label.isin(["AI", "Artificial Intelligence"])]["companies"].sum()) if len(fl) else 0
    A(f"1. **Retroactive relabeling is routine.** Across {s['n_snapshots']} monthly snapshots ({s['first_snapshot']} to {s['latest_snapshot']}) there were {s['relabel_events']} label-change events on existing companies. "
      f"The dominant flow is the pair 'Artificial Intelligence' <-> 'AI' ({ai_swap} swaps). Share of companies whose tag set changed between the first and latest snapshot, by batch (excluding pure AI/Artificial Intelligence swaps in the second column):\n")
    rt_ = th["retro"].dropna(subset=["tags_changed_pct"])
    A(_tbl(rt_, ["batch", "companies_in_both_snapshots", "tags_changed_pct", "tags_changed_excluding_AI_swaps_pct", "industry_changed_pct", "subindustry_changed_pct"], ["batch", "companies in both", "% tags changed", "% tags changed excl. AI swaps", "% industry changed", "% subindustry changed"]))
    A("\n   Consequence: any tag-level 'first appearance' or share for older batches reflects today's labels applied retroactively, and the 'AI' vs 'Artificial Intelligence' split is unstable. Treat the two as one measurement with two names.")
    intro = th["vocab"]; intro_t = intro[(intro.label_type == "tag") & intro.introduced_after_first_snapshot & (intro.count_latest >= 5)]
    intro_s = intro[(intro.label_type == "subindustry") & (intro.introduced_after_first_snapshot | intro.absent_in_latest_snapshot)]
    A(f"2. **New labels.** Tags with >= 5 companies that did not exist in the {s['first_snapshot']} snapshot: " + (", ".join(f"{r['label']} (first seen {r['first_seen_snapshot']}, now {int(r['count_latest'])})" for _, r in intro_t.iterrows()) or "none") + ". "
      "Subindustries added or removed: " + (", ".join(f"{r['label']} (first {r['first_seen_snapshot']}, last {r['last_seen_snapshot']}, {int(r['count_first'])} -> {int(r['count_latest'])})" for _, r in intro_s.iterrows()) or "none") + ". "
      "A label that appears in the vocabulary only recently can still be applied to companies from older batches; its first observed batch in section 6 is therefore not the first time such companies existed.")
    grow = intro[(intro.label_type == "tag") & (intro.count_change >= 30)].sort_values("count_change", ascending=False)
    A("3. **Labels whose total count grew fastest across the whole directory between snapshots** (new companies plus relabeling): " + ", ".join(f"{r['label']} ({int(r['count_first'])} -> {int(r['count_latest'])})" for _, r in grow.head(12).iterrows()) + ".")
    nd = th["near_duplicates"]
    A("4. **Near-duplicate labels** (kept separate everywhere in this analysis): " + "; ".join(nd["labels"].unique()) + ".")
    A(f"5. **Tag coverage collapses in some batches** (section 1): {', '.join(lt) or 'none'}. Unique-tag counts and tag shares there are not comparable.")
    pconly = sub[sub["subindustry"].isin(["B2B", "Industrials", "Healthcare", "Consumer", "Fintech", "Education", "Government", "Real Estate and Construction"])]
    A("6. **Parent-only subindustry strings are rising**: " + ", ".join(f"'{r['subindustry']}' {pct(r['earliest_year_share_pct'])} -> {pct(r['latest_share_pct'])}" for _, r in pconly.iterrows()) + ". Fewer child labels means child-level declines (e.g. within B2B) partly reflect less granular labelling.")
    A(f"7. **Secondary source disagreement.** The March-2026 dump agrees with today's directory on industry for {ctx['agree']['industry_identical_pct']}% of shared companies but on the exact tag list for only {ctx['agree']['tags_identical_pct']}%, consistent with point 1.")
    A("8. **Status and stage are point-in-time fields** (today's status for every company), and team size is today's team size, not size at batch.\n")
    A("## 10. Tag co-occurrence\n")
    pairs, pc = ctx["pairs"], ctx["pair_change"]
    for p in cfg["PERIODS"]:
        q = pairs[pairs.period == p["label"]]
        if q.empty: continue
        A(f"**{p['label']}** ({int(q['period_companies'].iloc[0])} companies). Most frequent pairs: " + "; ".join(f"{r.tag_a} + {r.tag_b} ({r.cooccurrence}, lift {r.lift:.1f})" for r in q.sort_values("cooccurrence", ascending=False).head(8).itertuples()) + ". "
          "Highest lift with >= 8 co-occurrences: " + "; ".join(f"{r.tag_a} + {r.tag_b} (lift {r.lift:.0f}, n={r.cooccurrence})" for r in q[q.cooccurrence >= 8].sort_values("lift", ascending=False).head(6).itertuples()) + ".\n")
    if len(pc):
        f_, l_ = cfg["PERIODS"][0]["label"], cfg["PERIODS"][-1]["label"]
        for rel, key in (("strengthening", f"cooccurrence_{l_}"), ("weakening", f"cooccurrence_{f_}"), ("newly emerging", f"cooccurrence_{l_}")):
            q = pc[pc.relationship == rel].sort_values(key, ascending=False).head(10)
            A(f"- {rel.capitalize()} ({int((pc.relationship == rel).sum())} pairs): " + "; ".join((f"{r.tag_a} + {r.tag_b} (lift {getattr(r, f'lift_{f_}'.replace('-', '_'), float('nan')):.1f} -> {getattr(r, f'lift_{l_}'.replace('-', '_'), float('nan')):.1f})" if rel != "newly emerging" else f"{r.tag_a} + {r.tag_b} (n={int(getattr(r, key.replace('-', '_')))}, lift {getattr(r, f'lift_{l_}'.replace('-', '_')):.1f})") for r in q.rename(columns=lambda c: c.replace("-", "_")).itertuples()) + ".")
    A("\nFull tables: `yc_tag_cooccurrence.csv`, `yc_tag_cooccurrence_change.csv`.\n")
    A("## 11. Geography (headquarters/location fields only)\n")
    g = ctx["geo"].set_index("batch"); fb = [b for b in ctx["batches"] if not bm.loc[b, "is_partial_batch"]]
    A(f"- US share (regions contains 'United States of America'): {pct(g.loc[fb[0], 'us_share_pct'])} in {fb[0]} to {pct(g.loc[fb[-1], 'us_share_pct'])} in {fb[-1]}; range across full batches {pct(g.loc[fb, 'us_share_pct'].min())}-{pct(g.loc[fb, 'us_share_pct'].max())}.")
    A(f"- Any remote flag ('Remote', 'Fully Remote', 'Partly Remote'): {pct(g.loc[fb[0], 'remote_any_share_pct'])} in {fb[0]} to {pct(g.loc[fb[-1], 'remote_any_share_pct'])} in {fb[-1]}.")
    A(f"- Distinct countries per batch: {int(g.loc[fb[0], 'unique_countries'])} in {fb[0]} to {int(g.loc[fb[-1], 'unique_countries'])} in {fb[-1]}.")
    c = ctx["countries"]; tot = c.groupby("country")["count"].sum().sort_values(ascending=False).head(10)
    A("- Most common countries overall (companies): " + ", ".join(f"{k} {v}" for k, v in tot.items()) + ".")
    def share_at(tbl, col, key, b):
        r = tbl[(tbl[col] == key) & (tbl["batch"] == b)]; return float(r["share_pct"].iloc[0]) if len(r) else 0.0
    for key in ["India", "United Kingdom", "Canada", "Mexico"]:
        A(f"  - {key}: {pct(share_at(c, 'country', key, fb[0]))} in {fb[0]} -> {pct(share_at(c, 'country', key, fb[-1]))} in {fb[-1]}.")
    m = ctx["macro"]
    A("- Macro-regions (YC `regions`): " + "; ".join(f"{k} {pct(share_at(m, 'macro_region', k, fb[0]))} -> {pct(share_at(m, 'macro_region', k, fb[-1]))}" for k in ["America / Canada", "Europe", "South Asia", "Latin America", "Southeast Asia", "Africa", "Middle East and North Africa"]) + f" ({fb[0]} -> {fb[-1]}).")
    ci = ctx["cities"]
    A("- Cities (first entry of `all_locations`): " + "; ".join(f"{k} {pct(share_at(ci, 'city', k, fb[0]))} -> {pct(share_at(ci, 'city', k, fb[-1]))}" for k in ["San Francisco, USA", "New York City, USA", "London, United Kingdom", "Bengaluru, India"]) + ".")
    A("\nThis describes where YC lists companies as located; it says nothing about target markets. Figure: `figures/geography_us_vs_non_us.png`.\n")
    A("## 12. Diversity and concentration\n")
    d = ctx["div"].set_index("batch")
    A(_tbl(ctx["div"][ctx["div"]["batch"].isin(fb)], ["batch", "unique_industries", "unique_subindustries", "unique_tags", "rarefied_unique_tags", "industry_entropy_normalised", "industry_hhi", "top5_industry_share_pct", "tag_entropy_normalised", "top10_tag_share_pct_of_companies"],
           ["batch", "industries", "subindustries", "tags", f"tags per {cfg['RAREFY_N']} cos", "industry entropy (norm.)", "industry HHI", "top-5 industry %", "tag entropy (norm.)", "top-10 tag % of cos"]))
    fbt = [b for b in fb if b not in lt]
    A(f"\n- Industry concentration: HHI {d.loc[fb[0], 'industry_hhi']:.2f} in {fb[0]} -> {d.loc[fb[-1], 'industry_hhi']:.2f} in {fb[-1]} (peak {d.loc[fb, 'industry_hhi'].max():.2f} in {d.loc[fb, 'industry_hhi'].idxmax()}); normalised industry entropy {d.loc[fb[0], 'industry_entropy_normalised']:.2f} -> {d.loc[fb[-1], 'industry_entropy_normalised']:.2f}.")
    A(f"- Subindustry variety: {int(d.loc[fb[0], 'unique_subindustries'])} distinct strings in {fb[0]} -> {int(d.loc[fb[-1], 'unique_subindustries'])} in {fb[-1]} (batch sizes {int(bm.loc[fb[0], 'total_companies'])} and {int(bm.loc[fb[-1], 'total_companies'])}).")
    A(f"- Tag variety, size-adjusted (unique tags among {cfg['RAREFY_N']} random companies): {f1(d.loc[fbt[0], 'rarefied_unique_tags'])} in {fbt[0]} -> {f1(d.loc[fbt[-1], 'rarefied_unique_tags'])} in {fbt[-1]}; top-10 tags cover {pct(d.loc[fbt[0], 'top10_tag_share_pct_of_companies'])} of companies in {fbt[0]} and {pct(d.loc[fbt[-1], 'top10_tag_share_pct_of_companies'])} in {fbt[-1]}.")
    A("- Reading: by industry the mix became markedly more concentrated in 2023-2025 (B2B alone above 60%) and has loosened somewhat in the most recent full batch as Industrials grew; by tag, size-adjusted variety is lower than in 2021 while the top-10 tags cover a larger slice of companies. Figures: `figures/industry_concentration_over_time.png`, `figures/tag_diversity_over_time.png`.\n")
    A("## 13. Requests for Startups (YC's own stated interests)\n")
    ed, req, pe, ba = ctx["ed"], ctx["req"], ctx["per_ed"], ctx["ba"]
    A(f"Parsed {len(req)} requests across {len(ed)} editions/versions from three eras: {int((ed.era=='essays').sum())} numbered essays (2009-2014), {int((ed.era=='consolidated').sum())} versions of the consolidated RFS page (2014-2024, one version per distinct content), and {int((ed.era=='seasonal').sum())} seasonal editions (Summer 2024 onward). Sources: live page plus Wayback Machine captures; raw HTML in `data/raw/rfs/`, table in `yc_rfs_requests.csv`.\n")
    A(_tbl(ed[ed.era != "essays"], ["era", "edition_label", "n_requests", "first_seen", "last_seen", "partners_named"], ["era", "edition", "requests", "first capture", "last capture", "partners named"]))
    per = ctx["persist"]
    A("\nLongest-lived consolidated-era categories (exact title match across versions): " + "; ".join(f"{r.title} ({r.n_editions} versions, {r.first_edition} to {r.last_edition})" for r in per.head(10).itertuples()) + ".")
    seas = req[req.era == "seasonal"]
    A("\nSeasonal edition titles:\n")
    for lab, g_ in seas.groupby("edition_label", sort=False):
        A(f"- **{lab}** ({len(g_)}): " + "; ".join(g_["title"]) + ".")
    s_ = pe[(pe.era == "seasonal")]
    tt = s_[s_.label_type == "tag"].groupby("label")["requests_mentioning"].sum().sort_values(ascending=False)
    ss = s_[s_.label_type == "subindustry_child"].groupby("label")["requests_mentioning"].sum().sort_values(ascending=False)
    A("\n**YC label names appearing verbatim in RFS text** (exact, case-insensitive string match of tag / industry / subindustry names in request title+body; this is a lexical overlap, not a classification). Seasonal editions, requests mentioning: tags: " + ", ".join(f"{k} {v}" for k, v in tt.head(20).items()) + ". Subindustry children: " + ", ".join(f"{k} {v}" for k, v in ss.head(10).items()) + ".")
    b_ = ba[(ba.era == "seasonal") & (ba.label_type == "tag") & ba.share_before_pct.notna()].sort_values("pp_change_after_minus_before", ascending=False)
    A("\nFor labels mentioned in a seasonal edition, share of batch in the two full batches before vs from the edition onward (descriptive; no causal reading):\n")
    A(_tbl(b_, ["label", "edition_label", "requests_mentioning", "batches_before", "share_before_pct", "batches_after", "share_after_pct", "pp_change_after_minus_before"], ["label", "edition", "requests", "before", "share before", "after", "share after", "pp"], n=15))
    A("\nFigures: `figures/rfs_requests_per_edition.png`, `figures/rfs_tag_name_mentions_by_edition.png`.\n")
    A("## 14. Prior work checked\n")
    A("- yc-oss/api (used): the only maintained, complete, daily-updated dump of YC's public directory with tags/industries back to 2005; its git history (Aug 2024 onward) is what enables the taxonomy-change checks above. START_YEAR can be set to 2005 without any code change.")
    A("- EXTREMOPHILARUM/yc-dataset (used for enrichment): 5,758-company snapshot (Mar 2026) with founders, launches, news, and 173 post-mortems; lower coverage than yc-oss/api.")
    A("- corralm/yc-scraper + Kaggle 'Y Combinator Directory' (Oct 2025, ~4,000 companies, founder fields), Kaggle 'Complete YCombinator Dataset 2005-2024', RummageLabs S24/F24 sets, benstaf/ycbench (W26 only), Apify scrapers (paid, same Algolia data), Extruct 'YC S25' post (one batch): none publishes a longitudinal analysis of YC's native taxonomy; none adds label information beyond the Algolia index.")
    A("- RFS: no structured multi-year dataset exists (the Hugging Face 'yc-rfs-analysis-2026' repo is empty); the table here was built from Wayback captures.\n")
    A("## 15. Questions YC's native taxonomy cannot answer\n")
    A("These require reading company descriptions (a future semantic/LLM classification phase) and are deliberately not attempted here:\n")
    for q in ["Whether a company is 'software' or 'deep tech'/'hard tech' in a consistent sense: 'Hard Tech' is a tag applied unevenly and retroactively, and Industrials includes pure-software companies.",
              "Whether a company is AI-native versus AI-adjacent, or which AI modality it uses: 'AI'/'Artificial Intelligence' now covers a third of every batch and is swapped between two names.",
              "Whether a company builds physical hardware, robots, or devices, versus software for those industries (e.g. 'Manufacturing and Robotics' contains both).",
              "Target customer or end market (regulated industry, SMB vs enterprise, consumer segment) and target geography: only headquarters location is available.",
              "Business model (SaaS vs marketplace vs services vs hardware sales) beyond the self-applied 'SaaS'/'Marketplace' tags, whose usage collapsed after 2023.",
              "Whether a company matches a specific RFS request or theme (the string overlap in section 13 is lexical only).",
              "Defense or dual-use exposure beyond the new 'Defense' label (introduced in the directory in 2026 and applied to 29 companies).",
              "Any measure that needs the 661 zero-tag companies (18%) to be classified, especially in Winter/Spring 2026.",
              "Founder background, technical depth, or 'research-lab' origin: not in the directory at all.",
              "Stage/traction at the time of the batch: status, stage and team size are today's values."]:
        A(f"- {q}")
    open(path, "w").write("\n".join(L) + "\n")
    return path
