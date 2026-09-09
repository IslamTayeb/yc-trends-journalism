from __future__ import annotations

import pandas as pd
import streamlit as st

import charts as CH
import compute as C
import context as X
from views._common import download, era_sizes, exclusion_note

METRICS = {
    "unique_industries": "Unique top-level industries",
    "unique_subindustries": "Unique subindustries",
    "unique_tags": "Unique tags (raw)",
    "rarefied_unique_tags": "Unique tags, rarefied to a fixed sample",
    "mean_tags_per_company": "Mean tags per company",
    "industry_entropy_normalised": "Industry entropy (0–1)",
    "tag_entropy_normalised": "Tag entropy (0–1)",
    "industry_hhi": "Industry HHI (concentration)",
    "tag_hhi": "Tag HHI (concentration)",
    "top5_industry_share_pct": "Top-5 industry share (%)",
    "top10_tag_share_pct_of_companies": "Top-10 tag share of companies (%)",
}


def render() -> None:
    ctx = X.get()
    st.title("Concentration and variety")
    st.markdown("How spread out each batch is across YC's labels. Entropy near 1 = evenly spread; HHI high = concentrated. "
                "Raw unique-tag counts scale with batch size; the rarefied series resamples %d companies per batch (%d draws)."
                % (int(ctx.cfg["RAREFY_N"]), int(ctx.cfg["RAREFY_DRAWS"])))
    div = ctx.with_era(ctx.tables["diversity"])
    chosen = st.multiselect("Metrics", list(METRICS), default=["tag_entropy_normalised", "industry_hhi", "rarefied_unique_tags"],
                            format_func=METRICS.get, key="div_metrics")
    if not chosen:
        return
    rows = []
    for m in chosen:
        d = div[["batch", "pos", "batch_order", "is_partial_batch", "low_tag_coverage", "total_companies", m]].rename(columns={m: "value"})
        d["metric"] = METRICS[m]
        d["count"] = d["value"]
        d["total"] = d["total_companies"]
        rows.append(d)
    g = pd.concat(rows)
    g["metric"] = pd.Categorical(g["metric"], categories=[METRICS[m] for m in chosen], ordered=True)
    st.plotly_chart(CH.small_multiples(g.sort_values(["metric", "batch_order"]), "metric", "value", ctx.meta, ctx.eras,
                                       hollow_low_tag=True, ncols=min(3, len(chosen))), key="diversity_fig1", width="stretch")
    st.caption("Hollow markers: partial or low-tag-coverage batches, where tag-based metrics are unreliable.")

    st.subheader("By era (mean of batch values)")
    era_sizes(ctx, tag_based=True)
    exclusion_note(ctx, tag_based=True)
    num = C.numeric_by_era(div, list(METRICS), ctx.era_names, ctx.excluded(True))
    st.dataframe(num.rename(columns=METRICS), hide_index=True, width="stretch")
    download(num, "diversity_by_era.csv")
    with st.expander("Per-batch table"):
        st.dataframe(div[["batch", "era", "total_companies"] + list(METRICS)], hide_index=True, width="stretch")
