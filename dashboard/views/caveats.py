from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import charts as CH
import context as X
from views._common import download


def render() -> None:
    ctx = X.get()
    st.title("Caveats and provenance")
    cfg = ctx.cfg
    st.markdown(f"""
**What the labels are.** Each company's `industry`, `subindustry`, `tags` and `regions` exactly as YC publishes them in the
directory index. Nothing is merged, renamed or inferred. Near-duplicate labels (below) are listed, not collapsed.

**Flags.** A batch with fewer than **{cfg['MIN_FULL_BATCH']}** companies is *partial* (still in progress). A batch where more than
**{cfg['TAG_COVERAGE_MAX_ZERO_TAG_PCT']}%** of companies have no tags is *low tag coverage*. Both stay on every time axis with hollow
markers; the sidebar toggles decide whether they enter era tables.

**Missing tags are removals, not a backlog.** Winter 2026 and Spring 2026 were almost fully tagged in the snapshots from
February to June 2026; by July 2026 roughly 80% of their companies had an empty tag list while `industry` and `subindustry` were
untouched. Fall 2025 went from 1% to about 20% zero-tag over the same months. The Summer 2026 batch is fully tagged. Treat tag
shares for those batches as YC data withheld, not as companies without a category.

**Retroactive relabeling.** YC edits labels on old companies. Monthly snapshots of the source since {ctx.prov.get('historical_snapshots', [['', '']])[0][1][:10] or '2024-08-22'}
show how much each batch's labels changed between the first snapshot and the latest. The dashboard shows the *latest* labels.
""")

    rl = ctx.with_era(ctx.tables["relabel_by_batch"])
    rows = []
    for col, name in {"tags_changed_pct": "Companies with tag changes (%)",
                      "tags_changed_excluding_AI_swaps_pct": "… excluding AI ↔ Artificial Intelligence swaps (%)",
                      "industry_changed_pct": "Companies with industry changes (%)",
                      "subindustry_changed_pct": "Companies with subindustry changes (%)"}.items():
        d = rl[["batch", "pos", "batch_order", "is_partial_batch", "low_tag_coverage", "companies_in_both_snapshots", col]]
        d = d.rename(columns={col: "share_pct", "companies_in_both_snapshots": "total"})
        d["count"] = (d["share_pct"] * d["total"] / 100).round()
        d["metric"] = name
        rows.append(d)
    g = pd.concat(rows)
    g = g[g['batch'].isin(ctx.plot_meta['batch'])]
    g["metric"] = pd.Categorical(g["metric"], categories=[r["metric"].iloc[0] for r in rows], ordered=True)
    st.subheader("Share of each batch relabeled since the first snapshot")
    st.plotly_chart(CH.lines_by_batch(g.sort_values(["metric", "batch_order"]), "metric", "share_pct", ctx.meta, ctx.eras,
                                      y_title="% of companies present in both snapshots", events=ctx.events), key="caveats_fig1", width="stretch")
    download(rl, "retroactive_relabeling_by_batch.csv")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tag coverage by batch")
        m = ctx.meta
        st.dataframe(m[["batch_code", "total_companies", "zero_tag_companies", "zero_tag_pct", "is_partial_batch", "low_tag_coverage"]],
                     hide_index=True, width="stretch", height=400)
    with c2:
        st.subheader("Largest tag relabel flows")
        st.dataframe(ctx.tables["relabel_flows"].head(25), hide_index=True, width="stretch", height=400)

    st.subheader("Near-duplicate YC labels (listed, never merged)")
    st.dataframe(ctx.tables["near_duplicates"], hide_index=True, width="stretch")

    st.subheader("Label vocabulary across snapshots")
    th = ctx.tables["taxonomy_history"]
    lt = st.radio("Label type", sorted(th["label_type"].unique()), horizontal=True, key="cv_lt")
    sub = th[th["label_type"] == lt]
    intro = sub[sub["introduced_after_first_snapshot"].astype(bool)][["label", "first_seen_snapshot", "count_latest"]]
    gone = sub[sub["absent_in_latest_snapshot"].astype(bool)][["label", "last_seen_snapshot", "count_first"]]
    a, b = st.columns(2)
    a.markdown("**Introduced after the first snapshot**")
    a.dataframe(intro, hide_index=True, width="stretch")
    b.markdown("**Absent in the latest snapshot**")
    b.dataframe(gone, hide_index=True, width="stretch")
    download(th, "taxonomy_history.csv")

    st.subheader("Provenance")
    st.code(json.dumps({k: v for k, v in ctx.prov.items() if k != "historical_snapshots"}, indent=1), language="json")
    st.caption(f"{len(ctx.prov.get('historical_snapshots', []))} historical snapshots used for relabel detection. "
               "Source data lives in data/all_years/processed; this app only reads it.")
