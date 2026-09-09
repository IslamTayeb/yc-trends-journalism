"""Small UI helpers shared by the views."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import compute as C
from context import Ctx

LABEL_TYPES = {"industry": "Industry (top level)", "subindustry": "Subindustry", "tag": "Tag"}
TAG_CAVEAT = ("Tags are YC's, kept verbatim. `AI` and `Artificial Intelligence` are separate YC labels that YC swaps "
              "between constantly; read them as one measurement. See **Caveats & provenance**.")


def download(df: pd.DataFrame, name: str, label: str = "Download CSV") -> None:
    st.download_button(label, df.to_csv(index=False).encode(), file_name=name, mime="text/csv", key=f"dl_{name}")


def era_sizes(ctx: Ctx, tag_based: bool = False) -> None:
    """Metric row: companies per era after exclusions, so comparisons are read with sizes in mind."""
    tot = C.era_totals(ctx.companies, ctx.measure, ctx.excluded(tag_based))
    cols = st.columns(max(len(ctx.era_names), 1))
    for col, name in zip(cols, ctx.era_names):
        e = next((e for e in ctx.eras if e.name == name), None)
        sub = f"{e.start_batch.replace(' ', ' ')} → {e.end_batch}" if e else f"{ctx.meta.iloc[0]['batch']} → {ctx.meta.iloc[-1]['batch']}"
        col.metric(name, f"{int(tot.get(name, 0)):,}", sub, delta_color="off")


def exclusion_note(ctx: Ctx, tag_based: bool = False) -> None:
    ex = ctx.excluded(tag_based)
    if ex:
        codes = ctx.meta.set_index("batch").loc[list(ex), "batch_code"].tolist()
        st.caption(f"Excluded from era tables: {', '.join(codes)} "
                   f"({'partial and/or low tag coverage' if tag_based else 'partial batches'}). "
                   "Toggle in the sidebar. They remain on time-axis charts as hollow markers.")
    else:
        st.caption("No batches excluded. Hollow markers on time-axis charts flag partial or low-tag-coverage batches.")


def need_eras(ctx: Ctx) -> bool:
    if not ctx.has_eras:
        st.info("Define at least two eras in the sidebar (pick the batches where a new era starts) to use this page.")
        return True
    return False


def label_picker(ctx: Ctx, label_type: str, by_batch: pd.DataFrame, col: str, key: str,
                 default_n: int = 8) -> list[str]:
    """Multiselect over labels present in the window, with a 'top N' shortcut."""
    totals = by_batch.groupby(col)["count"].sum().sort_values(ascending=False)
    options = totals.index.tolist()
    standalone = ctx.cfg.get({"industry": "STANDALONE_INDUSTRIES", "subindustry": "STANDALONE_SUBINDUSTRIES",
                              "tag": "STANDALONE_TAGS"}[label_type], [])
    if label_type == "subindustry":  # config lists children; the table holds "Parent -> Child"
        standalone = [o for o in options if o.split(" -> ")[-1] in standalone]
    default = [s for s in standalone if s in options][:default_n] or options[:default_n]
    c1, c2 = st.columns([3, 1])
    mode = c2.radio("Selection", ["Pick labels", "Top N by count"], key=f"{key}_mode", horizontal=False)
    if mode == "Top N by count":
        n = c2.slider("N", 3, 30, 10, key=f"{key}_topn")
        chosen = options[:n]
        c1.multiselect("Labels", options, default=chosen, disabled=True, key=f"{key}_ms_ro",
                       format_func=lambda o: f"{o} ({totals[o]})")
    else:
        chosen = c1.multiselect("Labels", options, default=default, key=f"{key}_ms",
                                format_func=lambda o: f"{o} ({totals[o]})")
    return chosen


def trend_toggle(ctx: Ctx, tag_based: bool = False) -> str | None:
    """On/off switch for dashed linear-fit trend lines on every series in the chart below. Shared across pages."""
    on = st.toggle("Trend lines", value=st.session_state.get("trend_on", False), key="trend_on",
                   help="Least-squares line per series, fitted on solid points only (partial batches"
                        + (" and low-tag-coverage batches" if tag_based else "") + " are left out of the fit).")
    ctx.trend = "linear" if on else None
    return ctx.trend
