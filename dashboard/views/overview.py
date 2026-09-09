from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import download, exclusion_note


def render() -> None:
    ctx = X.get()
    st.title("YC batch composition, by your eras")
    st.markdown(
        "Every view uses YC's own labels for each company (industry, subindustry, tags, regions, status) as published "
        "in the YC directory. Define eras in the sidebar; the charts shade them and the tables re-aggregate."
    )
    m = ctx.meta
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Batches in window", len(m), f"{m.iloc[0]['batch_code']} → {m.iloc[-1]['batch_code']}", delta_color="off")
    c2.metric("Companies", f"{len(ctx.companies):,}")
    c3.metric("Eras defined", len(ctx.eras))
    c4.metric("Partial / low-tag batches", f"{int(m['is_partial_batch'].sum())} / {int(m['low_tag_coverage'].sum())}")

    st.subheader("Batch sizes")
    fig = go.Figure(go.Bar(
        x=m["pos"], y=m["total_companies"],
        marker=dict(color=[ctx.colors.get(e, CH.PAL[0]) for e in m["era"]],
                    line=dict(color=[CH.INK2 if p else "rgba(0,0,0,0)" for p in m["is_partial_batch"]], width=1.5),
                    pattern=dict(shape=["/" if p else "" for p in m["is_partial_batch"]])),
        customdata=m[["batch", "era", "zero_tag_pct"]].values,
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>%{y} companies · %{customdata[2]}% without tags<extra></extra>",
    ))
    CH.add_era_bands(fig, ctx.eras)
    CH.batch_axis(fig, m)
    CH.style(fig, height=380, y_title="companies in batch", legend=False)
    fig.update_layout(hovermode="closest")
    st.plotly_chart(fig, key="overview_fig1", width="stretch")
    st.caption("Hatched bars: partial (in-progress) batches. Counts are companies with a public YC directory profile, not every company accepted.")

    st.subheader("Era summary")
    exclusion_note(ctx)
    summ = C.era_summary(ctx.companies[~ctx.companies["batch"].isin(ctx.excluded())],
                         ctx.industries, ctx.meta, ctx.era_names)
    st.dataframe(summ, width="stretch", hide_index=True)
    download(summ, "era_summary.csv")

    st.subheader("Top-level industry mix by era")
    ind, col = ctx.long("industry")
    be = C.label_by_era(ind, col, ctx.companies, "share", ctx.excluded())
    be["era"] = be["era"].astype(str)
    be = be.sort_values(["era", "share_pct"], ascending=[True, False])
    wide = C.era_wide(be, col, ctx.era_names)
    fig2 = go.Figure()
    for i, lab in enumerate(wide.sort_values(wide.columns[-1], ascending=False).index):
        fig2.add_trace(go.Bar(x=list(wide.columns), y=wide.loc[lab], name=lab, marker_color=CH.PAL[i % len(CH.PAL)],
                              hovertemplate=f"{lab}: %{{y:.1f}}%<extra></extra>"))
    CH.style(fig2, height=420, y_title="share of era companies (%)")
    fig2.update_layout(barmode="stack", hovermode="x unified")
    st.plotly_chart(fig2, key="overview_fig2", width="stretch")
    st.dataframe(wide.round(1), width="stretch")
    st.caption("`industry` is YC's single top-level label per company, so shares sum to ~100% within an era.")
