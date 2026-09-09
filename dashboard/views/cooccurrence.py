from __future__ import annotations

import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import TAG_CAVEAT, download, era_sizes, exclusion_note


def render() -> None:
    ctx = X.get()
    st.title("Tag co-occurrence by era")
    st.markdown("Which YC tags appear together on the same company, per era. "
                "Lift = observed pairs ÷ expected if the two tags were independent; Jaccard = shared ÷ union.")
    era_sizes(ctx, tag_based=True)
    exclusion_note(ctx, tag_based=True)
    c1, c2 = st.columns(2)
    min_tag = c1.slider("Min companies per tag (within era)", 3, 50, int(ctx.cfg["COOC_MIN_TAG_COMPANIES"]), key="co_mt")
    min_pair = c2.slider("Min pair count", 2, 30, int(ctx.cfg["COOC_MIN_PAIR_COUNT"]), key="co_mp")
    cooc = C.cooccurrence_by_era(ctx.tags, min_tag, min_pair, ctx.excluded(True))
    if cooc.empty:
        st.info("No pairs pass the thresholds.")
        return

    st.subheader("Pairs within one era")
    e1, e2, e3 = st.columns([2, 1, 1])
    era = e1.selectbox("Era", ctx.era_names, key="co_era")
    sort_by = e2.radio("Sort by", ["lift", "cooccurrence", "jaccard"], horizontal=True, key="co_sort")
    k = e3.slider("Show", 10, 60, 25, key="co_k")
    tag_filter = st.text_input("Only pairs involving tag (optional, exact YC tag)", key="co_tag").strip()
    sub = cooc[cooc["era"] == era]
    if tag_filter:
        sub = sub[(sub["tag_a"] == tag_filter) | (sub["tag_b"] == tag_filter)]
    sub = sub.sort_values(sort_by, ascending=False).head(k).copy()
    sub["pair"] = sub["tag_a"] + " + " + sub["tag_b"]
    st.plotly_chart(CH.bars(sub, "pair", sort_by, orientation="h", height=max(320, 22 * len(sub) + 80), y_title=sort_by),
                    width="stretch")
    st.dataframe(sub.drop(columns=["pair"]), hide_index=True, key="cooccurrence_fig1", width="stretch")
    download(cooc, "tag_cooccurrence_by_era.csv")

    if len(ctx.era_names) >= 2:
        st.subheader("How pairs changed between two eras")
        a, b = st.columns(2)
        era_a = a.selectbox("Era A", ctx.era_names, index=0, key="co_a")
        era_b = b.selectbox("Era B", ctx.era_names, index=len(ctx.era_names) - 1, key="co_b")
        if era_a != era_b:
            pc = C.pair_change(cooc, era_a, era_b, int(ctx.cfg["COOC_NEW_PAIR_MAX_EARLY"]), min_pair)
            rels = st.multiselect("Relationship", sorted(pc["relationship"].unique()),
                                  default=[r for r in ["strengthening", "weakening", "newly emerging"] if r in set(pc["relationship"])],
                                  key="co_rel")
            shown = pc[pc["relationship"].isin(rels)].sort_values("lift_change", ascending=False)
            st.dataframe(shown, hide_index=True, width="stretch")
            st.caption("Rules mirror the pipeline: newly emerging = ≤ %d pairs in A and ≥ %d in B; disappeared = the reverse; "
                       "strengthening / weakening = lift change of ±0.5 or more. Absolute pair thresholds favour the larger era, "
                       "so read 'disappeared' against the era sizes shown above." % (int(ctx.cfg["COOC_NEW_PAIR_MAX_EARLY"]), min_pair))
            download(pc, f"pair_change_{era_a}_vs_{era_b}.csv".replace(" ", "_"))
    st.caption(TAG_CAVEAT)
