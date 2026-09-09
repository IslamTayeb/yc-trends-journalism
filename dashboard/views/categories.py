from __future__ import annotations

import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import LABEL_TYPES, TAG_CAVEAT, download, exclusion_note, label_picker


def render() -> None:
    ctx = X.get()
    st.title("Categories over time")
    lt = st.radio("Label type", list(LABEL_TYPES), format_func=LABEL_TYPES.get, horizontal=True, key="cat_lt")
    tag_based = lt == "tag"
    long_df, col = ctx.long(lt)
    measure = ctx.measure if (tag_based or ctx.measure != "tagged") else "share"
    by_batch = C.label_by_batch(long_df, col, ctx.meta, measure)
    labels = label_picker(ctx, lt, by_batch, col, key=f"cat_{lt}")
    if not labels:
        st.info("Pick at least one label.")
        return
    g = C.grid(by_batch, col, labels, ctx.plot_meta)
    vcol = ctx.value_col()
    ytitle = C.MEASURES[measure]

    view = st.radio("Layout", ["One chart", "Small multiples"], horizontal=True, key="cat_layout", label_visibility="collapsed")
    if view == "One chart":
        fig = CH.lines_by_batch(g, col, vcol, ctx.plot_meta, ctx.eras, hollow_low_tag=tag_based, y_title=ytitle)
    else:
        fig = CH.small_multiples(g, col, vcol, ctx.plot_meta, ctx.eras, hollow_low_tag=tag_based, y_title=ytitle)
    st.plotly_chart(fig, key="categories_fig1", width="stretch")
    st.caption("Hollow markers: partial batches" + (" or low tag coverage batches" if tag_based else "") +
               ". Each point is one batch. " + (TAG_CAVEAT if tag_based else ""))

    st.subheader("By era")
    exclusion_note(ctx, tag_based)
    be = C.label_by_era(long_df, col, ctx.companies, measure, ctx.excluded(tag_based))
    wide = C.era_wide(be, col, ctx.era_names, value=vcol).reindex(labels).fillna(0)
    counts = C.era_wide(be, col, ctx.era_names, value="count").reindex(labels).fillna(0).astype(int)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(CH.heatmap(wide.round(1), value_title=ytitle), key="categories_fig2", width="stretch")
    with c2:
        st.dataframe(wide.round(2), width="stretch")
        st.dataframe(counts, width="stretch")
    download(be[be[col].isin(labels)], f"{lt}_by_era.csv")

    with st.expander(f"Top {lt} labels per batch (rank chart)"):
        n = st.slider("Top N", 5, 25, 10, key="cat_bump_n")
        top = C.top_per_batch(by_batch, col, n)
        st.plotly_chart(CH.bump(top[top['batch'].isin(ctx.plot_meta['batch'])], col, ctx.plot_meta, ctx.eras, n), key="categories_fig3", width="stretch")
        st.caption("Rank by count within each batch; a line breaks where the label drops out of the top N.")
        download(top, f"{lt}_top_per_batch.csv")

    with st.expander("Full label × batch table"):
        full = by_batch.pivot_table(index=col, columns="batch_code", values=vcol, aggfunc="first").fillna(0)
        full = full[ctx.meta["batch_code"].tolist()]
        st.dataframe(full.round(2), width="stretch")
        download(by_batch, f"{lt}_by_batch.csv")
