"""Run the whole native-taxonomy pipeline. Stages are functions so they can be re-run individually."""
from __future__ import annotations
import json, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import pandas as pd
from ycnative.config import load_config, ROOT
from ycnative import load, batches as B, taxonomy as T, trends as TR, rankings as RK, cooccurrence as CO, geography as G, diversity as D, fetch as F
from ycnative import taxonomy_history as TH, enrichment as EN, quality as Q, rfs as RFS, figures as FIG, workbook as WB, report as RP

def main(stages=None):
    cfg = load_config(); OUT = cfg["OUT"]
    t0 = time.time()
    prov = F.write_provenance()
    records = load.read_all()
    df_all = load.to_frame(records)
    df, excluded = load.select_window(df_all, cfg["START_YEAR"], cfg["END_YEAR"], cfg["MIN_FULL_BATCH"])
    batches = load.batch_order(df)
    print(f"selected {len(df)} companies in {len(batches)} batches ({batches[0]} .. {batches[-1]}); excluded {len(excluded)}")
    tags_long, inds_long, subs_long = load.long_tables(df)
    load.companies_csv(df).to_csv(OUT / "yc_companies_native.csv", index=False)
    tags_long.to_csv(OUT / "yc_company_tags.csv", index=False)
    inds_long.to_csv(OUT / "yc_company_industries.csv", index=False)
    subs_long.to_csv(OUT / "yc_company_subindustries.csv", index=False)
    # batch summary
    bs = B.batch_summary(df); bs.to_csv(OUT / "yc_batch_summary.csv", index=False)
    bmeta = bs[["batch", "batch_code", "year", "batch_order", "total_companies", "is_partial_batch"]]
    # taxonomy inventory + cross-check
    ind_inv, sub_inv, ind_arr_inv, tag_inv, tax_summary = T.inventory(df, tags_long, inds_long, subs_long)
    ind_inv.to_csv(OUT / "yc_industries.csv", index=False); sub_inv.to_csv(OUT / "yc_subindustries.csv", index=False)
    ind_arr_inv.to_csv(OUT / "yc_industries_array_membership.csv", index=False); tag_inv.to_csv(OUT / "yc_tags.csv", index=False)
    json.dump(tax_summary, open(OUT / "yc_taxonomy_summary.json", "w"), indent=1)
    xc = T.cross_check(records, df_all); xc.to_csv(ROOT / "data" / "quality" / "source_cross_check.csv", index=False)
    print("cross-check mismatches:", int((~xc["match"]).sum()), "of", len(xc))
    # batches whose tag coverage is unreliable (share of zero-tag companies above threshold)
    bs["zero_tag_pct"] = (100 * bs["zero_tag_companies"] / bs["total_companies"]).round(1)
    bs["low_tag_coverage"] = bs["zero_tag_pct"] > cfg["TAG_COVERAGE_MAX_ZERO_TAG_PCT"]
    low_tag_batches = bs.loc[bs["low_tag_coverage"], "batch"].tolist()
    bs.to_csv(OUT / "yc_batch_summary.csv", index=False)
    print("low tag coverage batches:", low_tag_batches)
    # trends: industry (top-level), subindustry (full string), tag
    results = {}
    for name, long_df, col in (("industry", inds_long[inds_long["level"] == "top"], "industry"),
                               ("subindustry", subs_long, "subindustry"), ("tag", tags_long, "tag")):
        counts, shares, sizes = TR.matrices(long_df, col, df, batches)
        counts.to_csv(OUT / f"yc_{name}_by_batch_counts.csv"); shares.to_csv(OUT / f"yc_{name}_by_batch_share.csv")
        ycounts, yshares, ysizes = TR.year_matrices(long_df, col, df)
        ycounts.to_csv(OUT / f"yc_{name}_by_year_counts.csv"); yshares.to_csv(OUT / f"yc_{name}_by_year_share.csv")
        long = TR.to_long(counts, shares, name, bmeta); long.to_csv(OUT / f"yc_{name}_trends.csv", index=False)
        excl = low_tag_batches if name == "tag" else None
        stats = TR.trend_stats(counts, shares, bmeta, cfg, name, exclude_batches=excl); stats.to_csv(OUT / f"yc_{name}_trend_stats.csv", index=False)
        if name == "tag":
            tc, ts_, _ = TR.matrices_of_tagged(long_df, col, df, batches)
            ts_.to_csv(OUT / "yc_tag_by_batch_share_of_tagged.csv")
            results["tag_share_of_tagged"] = ts_
        topn = RK.top_n_per_batch(shares, counts, cfg["TOP_N_INDUSTRIES"] if name == "industry" else cfg["TOP_N_TAGS"], name)
        topn.to_csv(OUT / f"yc_{name}_top_per_batch.csv", index=False)
        rk = RK.rank_table(stats, name, cfg); rk.to_csv(OUT / f"yc_{name}_rankings.csv", index=False)
        results[name] = dict(counts=counts, shares=shares, stats=stats, long=long, topn=topn, rank=rk)
        print(f"{name}: {len(counts)} labels; emerging={int((stats.emergence_class=='Emerging').sum())} declining={int((stats.emergence_class=='Declining').sum())}")
    # co-occurrence
    pairs, pair_change = CO.cooccurrence(df, cfg)
    pairs.to_csv(OUT / "yc_tag_cooccurrence.csv", index=False); pair_change.to_csv(OUT / "yc_tag_cooccurrence_change.csv", index=False)
    # geography
    geo, countries, macro, cities = G.geography(df, bmeta)
    geo.to_csv(OUT / "yc_geography_trends.csv", index=False); countries.to_csv(OUT / "yc_geography_countries.csv", index=False)
    macro.to_csv(OUT / "yc_geography_macro_regions.csv", index=False); cities.to_csv(OUT / "yc_geography_cities.csv", index=False)
    # diversity
    div = D.diversity(df, bmeta, cfg); div.to_csv(OUT / "yc_diversity.csv", index=False)
    print(f"core stages done in {time.time()-t0:.1f}s")
    # taxonomy history (git snapshots of companies/all.json)
    th = TH.run(df, cfg)
    if th:
        th["vocab"].to_csv(OUT / "yc_taxonomy_history.csv", index=False); th["relabels"].to_csv(OUT / "yc_relabel_events.csv", index=False)
        th["retro"].to_csv(OUT / "yc_retroactive_relabeling_by_batch.csv", index=False); th["flows"].to_csv(OUT / "yc_tag_relabel_flows.csv", index=False)
        th["near_duplicates"].to_csv(OUT / "yc_near_duplicate_labels.csv", index=False)
        json.dump(th["summary"], open(OUT / "yc_taxonomy_history_summary.json", "w"), indent=1)
        print("taxonomy history:", th["summary"]["n_snapshots"], "snapshots;", th["summary"]["relabel_events"], "relabel events")
    # enrichment from secondary source (never overrides YC labels)
    df_enriched, agree, cov = EN.enrich(df)
    load.companies_csv(df_enriched).to_csv(OUT / "yc_companies_native.csv", index=False)
    cov.to_csv(ROOT / "data" / "quality" / "secondary_source_coverage.csv", index=False)
    json.dump(agree, open(ROOT / "data" / "quality" / "secondary_source_agreement.json", "w"), indent=1)
    print("secondary coverage:", agree)
    # RFS
    req, ed, persist = RFS.build()
    req.to_csv(OUT / "yc_rfs_requests.csv", index=False); ed.to_csv(OUT / "yc_rfs_editions.csv", index=False); persist.to_csv(OUT / "yc_rfs_title_persistence.csv", index=False)
    labels = {"tag": sorted(tags_long["tag"].unique()), "industry": sorted(df["n_industry_top"].dropna().unique()),
              "subindustry_child": sorted(df["n_subindustry_child"].dropna().unique())}
    mentions, per_ed = RFS.label_mentions(req, labels)
    mentions.to_csv(OUT / "yc_rfs_label_mentions_detail.csv", index=False); per_ed.to_csv(OUT / "yc_rfs_label_mentions.csv", index=False)
    ba = RFS.before_after(per_ed, results, bmeta, low_tag_batches)
    ba.to_csv(OUT / "yc_rfs_label_share_before_after.csv", index=False)
    print(f"RFS: {len(req)} requests in {len(ed)} editions; {len(per_ed)} label-edition mentions")
    # data quality + spot check
    dq = Q.dq_report(df_all, df, excluded, bs, tax_summary, xc, low_tag_batches, cfg); dq.to_csv(ROOT / "data" / "quality" / "data_quality_report.csv", index=False)
    sc = Q.spot_check(df, records); sc.to_csv(ROOT / "data" / "quality" / "spot_check_50.csv", index=False)
    n_bad = int((~sc["match"]).sum()); print(f"spot check: {sc['company_id'].nunique()} companies, {len(sc)} field comparisons, mismatches={n_bad}")
    if n_bad: raise SystemExit("spot check failed - see data/quality/spot_check_50.csv")
    ctx = dict(th=th, req=req, ed=ed, persist=persist, mentions=mentions, per_ed=per_ed, ba=ba, dq=dq, sc=sc, agree=agree, cov=cov, df_enriched=df_enriched, low_tag_batches=low_tag_batches, cfg=cfg,
               df=df, df_all=df_all, excluded=excluded, batches=batches, bs=bs, bmeta=bmeta, results=results,
               tags_long=tags_long, inds_long=inds_long, subs_long=subs_long, pairs=pairs, pair_change=pair_change,
               geo=geo, countries=countries, macro=macro, cities=cities, div=div, tax_summary=tax_summary, xc=xc, prov=prov,
               ind_inv=ind_inv, sub_inv=sub_inv, tag_inv=tag_inv, ind_arr_inv=ind_arr_inv, records=records)
    made = FIG.make_all(ctx); print(f"figures: {len(made)} written to {cfg['FIG']}")
    ctx["figures"] = made
    import os
    dest = cfg["OUT"].parent if os.environ.get("OUT_DIR") else ROOT   # keep root deliverables untouched when OUT_DIR is overridden
    WB.build(ctx, dest / "yc_native_analysis.xlsx"); print("workbook written")
    RP.build(ctx, dest / "report.md"); print("report written")
    print(f"all stages done in {time.time()-t0:.1f}s")
    return ctx

if __name__ == "__main__":
    main()
