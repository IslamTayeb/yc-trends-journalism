from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import download, era_sizes, exclusion_note


def _metric_grid(df: pd.DataFrame, metrics: dict[str, str], meta: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, name in metrics.items():
        d = df[["batch", col, "total_companies"]].rename(columns={col: "share_pct"})
        d["metric"] = name
        rows.append(d)
    g = pd.concat(rows).merge(meta[["batch", "pos", "batch_order", "is_partial_batch", "low_tag_coverage"]], on="batch")
    g["count"] = (g["share_pct"] * g["total_companies"] / 100).round().astype(int)
    g["total"] = g["total_companies"]
    g["metric"] = pd.Categorical(g["metric"], categories=list(metrics.values()), ordered=True)
    return g.sort_values(["metric", "batch_order"])


def render() -> None:
    ctx = X.get()
    st.title("Geography")
    st.markdown("From YC's `regions` field (countries, macro-regions and remote flags) and `all_locations`. "
                "Location is company HQ as listed by YC, not target market.")
    geo = ctx.with_era(ctx.tables["geo_trends"])
    metrics = {"us_share_pct": "US (United States of America in regions)", "non_us_share_pct": "Non-US",
               "remote_any_share_pct": "Any remote flag"}
    g = _metric_grid(geo, metrics, ctx.plot_meta)
    st.plotly_chart(CH.lines_by_batch(g, "metric", "share_pct", ctx.plot_meta, ctx.eras, y_title="share of batch (%)"),
                    width="stretch")

    st.subheader("By era")
    era_sizes(ctx)
    exclusion_note(ctx)
    num = C.numeric_by_era(geo, ["us_share_pct", "non_us_share_pct", "remote_any_share_pct", "unique_countries"],
                           ctx.era_names, ctx.excluded())
    st.dataframe(num, hide_index=True, key="geography_fig1", width="stretch")
    st.caption("Means of batch-level shares within each era (each batch weighted equally).")

    c1, c2 = st.columns(2)
    macro = C.geo_by_era(ctx.companies, ctx.with_era(ctx.tables["geo_macro"]), "macro_region", ctx.era_names, ctx.excluded())
    with c1:
        st.markdown("**Macro-regions** (YC's region strings that are not countries)")
        fig = go.Figure()
        regions = macro.groupby("macro_region")["count"].sum().sort_values(ascending=False).index
        for i, r in enumerate(regions):
            d = macro[macro["macro_region"] == r]
            fig.add_trace(go.Bar(x=d["era"].astype(str), y=d["share_pct"], name=r, marker_color=CH.PAL[i % len(CH.PAL)],
                                 hovertemplate=f"{r}: %{{y:.1f}}%<extra></extra>"))
        CH.style(fig, height=420, y_title="share of era companies (%)")
        fig.update_layout(barmode="group", hovermode="x unified")
        st.plotly_chart(fig, key="geography_fig2", width="stretch")
        st.caption("A company can list several regions (for example a country and its macro-region), so bars do not sum to 100%.")
    countries = C.geo_by_era(ctx.companies, ctx.with_era(ctx.tables["geo_countries"]), "country", ctx.era_names, ctx.excluded())
    with c2:
        st.markdown("**Countries** (top 20 by companies in window)")
        top = countries.groupby("country")["count"].sum().sort_values(ascending=False).head(20).index
        wide = countries[countries["country"].isin(top)].pivot_table(index="country", columns="era", values="share_pct",
                                                                     observed=True).reindex(top).fillna(0)
        wide = wide[[e for e in ctx.era_names if e in wide.columns]]
        st.plotly_chart(CH.heatmap(wide.round(1), value_title="share %"), key="geography_fig3", width="stretch")
    download(macro, "macro_regions_by_era.csv")
    download(countries, "countries_by_era.csv")

    with st.expander("Cities by era (top 25)"):
        cities = C.geo_by_era(ctx.companies, ctx.with_era(ctx.tables["geo_cities"]), "city", ctx.era_names, ctx.excluded())
        topc = cities.groupby("city")["count"].sum().sort_values(ascending=False).head(25).index
        widec = cities[cities["city"].isin(topc)].pivot_table(index="city", columns="era", values="share_pct",
                                                              observed=True).reindex(topc).fillna(0)
        st.dataframe(widec[[e for e in ctx.era_names if e in widec.columns]].round(1), width="stretch")
