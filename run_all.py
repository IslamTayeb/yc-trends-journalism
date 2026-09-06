"""Run the whole native-taxonomy pipeline. Stages are functions so they can be re-run individually."""
from __future__ import annotations
import json, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import pandas as pd
from ycnative.config import load_config, ROOT
from ycnative import load, batches as B, taxonomy as T, trends as TR, rankings as RK, cooccurrence as CO, geography as G, diversity as D, fetch as F

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
    # trends: industry (top-level), subindustry (full string), tag
    results = {}
    for name, long_df, col in (("industry", inds_long[inds_long["level"] == "top"], "industry"),
                               ("subindustry", subs_long, "subindustry"), ("tag", tags_long, "tag")):
        counts, shares, sizes = TR.matrices(long_df, col, df, batches)
        counts.to_csv(OUT / f"yc_{name}_by_batch_counts.csv"); shares.to_csv(OUT / f"yc_{name}_by_batch_share.csv")
        ycounts, yshares, ysizes = TR.year_matrices(long_df, col, df)
        ycounts.to_csv(OUT / f"yc_{name}_by_year_counts.csv"); yshares.to_csv(OUT / f"yc_{name}_by_year_share.csv")
        long = TR.to_long(counts, shares, name, bmeta); long.to_csv(OUT / f"yc_{name}_trends.csv", index=False)
        stats = TR.trend_stats(counts, shares, bmeta, cfg, name); stats.to_csv(OUT / f"yc_{name}_trend_stats.csv", index=False)
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
    return dict(cfg=cfg, df=df, df_all=df_all, excluded=excluded, batches=batches, bs=bs, bmeta=bmeta, results=results,
                tags_long=tags_long, inds_long=inds_long, subs_long=subs_long, pairs=pairs, pair_change=pair_change,
                geo=geo, countries=countries, macro=macro, cities=cities, div=div, tax_summary=tax_summary, xc=xc, prov=prov,
                ind_inv=ind_inv, sub_inv=sub_inv, tag_inv=tag_inv, ind_arr_inv=ind_arr_inv, records=records)

if __name__ == "__main__":
    main()
