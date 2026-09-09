"""Smoke test for the dashboard's data/compute layer (no UI). Run: uv run python dashboard/_smoke.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compute as C  # noqa: E402
import context as X  # noqa: E402
import eras as E  # noqa: E402


def check(cond, msg):
    if not cond:
        raise SystemExit(f"FAIL: {msg}")
    print(f"ok   {msg}")


def run(state, start_year, measure="share"):
    ctx = X.build(start_year, None, state, measure, True, True)
    n_win = len(ctx.companies)
    check(n_win > 0, f"window {start_year}+: {n_win} companies, {len(ctx.meta)} batches, eras={ctx.era_names}")
    check(ctx.companies["era"].notna().all(), "every company assigned an era")
    check(ctx.companies.groupby("era", observed=True).size().sum() == n_win, "era totals sum to window total")

    for lt in ("industry", "subindustry", "tag"):
        long_df, col = ctx.long(lt)
        bb = C.label_by_batch(long_df, col, ctx.meta, measure)
        labels = bb.groupby(col)["count"].sum().sort_values(ascending=False).head(6).index.tolist()
        g = C.grid(bb, col, labels, ctx.meta)
        check(len(g) == len(labels) * len(ctx.meta), f"{lt}: grid complete ({len(g)} rows)")
        be = C.label_by_era(long_df, col, ctx.companies, measure, ctx.excluded(lt == "tag"))
        check(not be.empty, f"{lt}: by-era table {be.shape}")
        w = C.era_wide(be, col, ctx.era_names)
        check(list(w.columns) == [e for e in ctx.era_names if e in w.columns], f"{lt}: era_wide columns ordered")
        if len(ctx.era_names) >= 2:
            cmp = C.era_compare(be, col, ctx.era_names[0], ctx.era_names[-1], min_count=5)
            check("pp_change" in cmp.columns and len(cmp) > 0, f"{lt}: era_compare {len(cmp)} labels")
        top = C.top_per_batch(bb, col, 10)
        check(top["rank"].max() <= 10, f"{lt}: top_per_batch")

    cooc = C.cooccurrence_by_era(ctx.tags, 10, 5, ctx.excluded(True))
    check(not cooc.empty and cooc["lift"].notna().all(), f"cooccurrence {len(cooc)} pairs across {cooc['era'].nunique()} eras")
    if len(ctx.era_names) >= 2:
        pc = C.pair_change(cooc, ctx.era_names[0], ctx.era_names[-1])
        check(pc["relationship"].notna().all(), f"pair_change relationships: {pc['relationship'].value_counts().to_dict()}")

    summ = C.era_summary(ctx.companies, ctx.industries, ctx.meta, ctx.era_names)
    check(summ["companies"].sum() == n_win, f"era_summary totals ({summ['companies'].tolist()})")
    macro = C.geo_by_era(ctx.companies, ctx.with_era(ctx.tables["geo_macro"]), "macro_region", ctx.era_names, ctx.excluded())
    check(not macro.empty, f"geo macro by era {macro.shape}")
    div = C.numeric_by_era(ctx.with_era(ctx.tables["diversity"]), ["tag_entropy_normalised", "industry_hhi", "rarefied_unique_tags"],
                           ctx.era_names, ctx.excluded())
    check(len(div) == len(ctx.era_names), f"diversity by era {div.shape}")

    # charts build without error
    import charts as CH
    long_df, col = ctx.long("tag")
    bb = C.label_by_batch(long_df, col, ctx.meta, measure)
    labels = bb.groupby(col)["count"].sum().sort_values(ascending=False).head(4).index.tolist()
    g = C.grid(bb, col, labels, ctx.meta)
    CH.lines_by_batch(g, col, ctx.value_col(), ctx.meta, ctx.eras, hollow_low_tag=True, trend="linear", events=ctx.events)
    CH.lines_by_batch(g, col, ctx.value_col(), ctx.meta, ctx.eras, trend="rolling", events=ctx.events)
    check(E.date_to_pos("2022-11", ctx.meta) is not None, f"event pos for 2022-11: {E.date_to_pos('2022-11', ctx.meta)} (events={[(e['month'], round(e['pos'],2)) for e in ctx.events]})")
    CH.small_multiples(g, col, ctx.value_col(), ctx.meta, ctx.eras)
    CH.heatmap(C.era_wide(C.label_by_era(long_df, col, ctx.companies, measure, ()), col, ctx.era_names).head(20))
    CH.bump(C.top_per_batch(bb, col, 10), col, ctx.meta, ctx.eras, 10)
    CH.diverging_bars(C.era_compare(C.label_by_era(long_df, col, ctx.companies, measure, ()), col,
                                    ctx.era_names[0], ctx.era_names[-1]).head(10), col, "pp_change")
    check(True, "charts built")
    return ctx


if __name__ == "__main__":
    run(E.empty_state(), 2021)
    st = {"cuts": ["Winter 2020", "Winter 2023", "Summer 2025"], "names": {"Winter 2023": "Post-GPT"}, "before_name": "Early"}
    ctx = run(st, 2016)
    print([ (e.name, e.start_batch, e.end_batch, e.n_batches) for e in ctx.eras])
    run(st, 2021, measure="count")
    run(st, 2005, measure="tagged")
    print("SMOKE OK")
