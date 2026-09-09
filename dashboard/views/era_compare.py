from __future__ import annotations

import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import LABEL_TYPES, TAG_CAVEAT, download, era_sizes, exclusion_note, need_eras


def render() -> None:
    ctx = X.get()
    st.title("Compare eras")
    if need_eras(ctx):
        return
    lt = st.radio("Label type", list(LABEL_TYPES), format_func=LABEL_TYPES.get, horizontal=True, key="cmp_lt")
    tag_based = lt == "tag"
    long_df, col = ctx.long(lt)
    measure = ctx.measure if (tag_based or ctx.measure != "tagged") else "share"
    if measure == "count":
        st.warning("Era sizes differ, so counts are not comparable across eras. Showing share instead.")
        measure = "share"
    era_sizes(ctx, tag_based)
    exclusion_note(ctx, tag_based)

    c1, c2, c3 = st.columns(3)
    era_a = c1.selectbox("Era A", ctx.era_names, index=0, key="cmp_a")
    era_b = c2.selectbox("Era B", ctx.era_names, index=len(ctx.era_names) - 1, key="cmp_b")
    min_count = c3.slider("Min companies (in either era)", 0, 50, 5, key="cmp_min")
    if era_a == era_b:
        st.info("Pick two different eras.")
        return
    be = C.label_by_era(long_df, col, ctx.companies, measure, ctx.excluded(tag_based))
    cmp = C.era_compare(be, col, era_a, era_b, min_count)
    if cmp.empty:
        st.info("No labels pass the minimum count.")
        return

    st.subheader(f"Movers: {era_a} → {era_b}")
    k = st.slider("Show top/bottom", 5, 40, 15, key="cmp_k")
    gain = cmp[cmp["pp_change"] > 0].head(k)
    loss = cmp[(cmp["pp_change"] < 0) & ~cmp[col].isin(gain[col])].tail(k)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**Largest gains** (pp of {C.MEASURES[measure].lower()})")
        st.plotly_chart(CH.diverging_bars(gain, col, "pp_change", x_title="percentage points"), key="era_compare_fig1", width="stretch")
    with r:
        st.markdown("**Largest losses**")
        if loss.empty:
            st.caption("No label lost share.")
        else:
          st.plotly_chart(CH.diverging_bars(loss, col, "pp_change", x_title="percentage points"), key="era_compare_fig2", width="stretch")
    st.markdown("**Ratio view** (share in B ÷ share in A; labels absent in A have no ratio)")
    ratio = cmp.dropna(subset=["ratio"]).sort_values("ratio", ascending=False)
    rr = st.columns(2)
    rr[0].dataframe(ratio.head(k)[[col, "ratio", "pp_change"]], hide_index=True, width="stretch")
    rr[1].dataframe(ratio.tail(k)[[col, "ratio", "pp_change"]], hide_index=True, width="stretch")

    st.subheader("Full comparison table")
    st.dataframe(cmp, width="stretch", hide_index=True)
    download(cmp, f"{lt}_compare_{era_a}_vs_{era_b}.csv".replace(" ", "_"))

    st.subheader("All eras at once")
    wide = C.era_wide(be, col, ctx.era_names)
    top_labels = wide.max(axis=1).sort_values(ascending=False).head(40).index
    st.plotly_chart(CH.heatmap(wide.loc[top_labels].round(1), value_title=C.MEASURES[measure]), key="era_compare_fig3", width="stretch")
    st.caption("Top 40 labels by peak era share." + (" " + TAG_CAVEAT if tag_based else ""))
    download(wide.reset_index(), f"{lt}_by_era_wide.csv")
