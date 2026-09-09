from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts as CH
import context as X
from views._common import download

SEASON_MONTH = {"Winter": 1, "Spring": 4, "Summer": 6, "Fall": 9}


def _batch_date(batch: str) -> dt.date:
    season, year = batch.split()
    return dt.date(int(year), SEASON_MONTH[season], 1)


def _ts_date(ts) -> dt.date | None:
    s = str(ts)
    if len(s) < 8 or not s[:8].isdigit():
        return None
    return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def render() -> None:
    ctx = X.get()
    st.title("Requests for Startups")
    st.markdown("YC's own published wish-lists: essay era (2009–2013), the consolidated page (2014–2024, versions by "
                "first-seen Wayback capture) and seasonal editions (Summer 2024 on). Shown on a calendar axis with your eras shaded.")
    ed = ctx.tables["rfs_editions"].copy()
    ed["date"] = ed["first_seen"].apply(_ts_date)
    ed = ed.dropna(subset=["date"]).sort_values("date")

    fig = go.Figure(go.Bar(x=ed["date"], y=ed["n_requests"], name="requests in edition",
                           marker_color=[CH.PAL[{"essays": 3, "consolidated": 0, "seasonal": 1}.get(e, 4)] for e in ed["era"]],
                           customdata=ed[["edition_label", "era"]].values,
                           hovertemplate="%{customdata[0]} (%{customdata[1]})<br>first seen %{x|%Y-%m-%d}<br>%{y} requests<extra></extra>"))
    # era bands on calendar axis
    for e in ctx.eras:
        x0 = _batch_date(e.start_batch)
        nxt = ctx.meta[ctx.meta["pos"] == e.end_pos + 1]
        x1 = _batch_date(nxt.iloc[0]["batch"]) if len(nxt) else _batch_date(e.end_batch) + dt.timedelta(days=120)
        fig.add_vrect(x0=x0, x1=x1, fillcolor=e.color, opacity=0.09, line_width=0, layer="below",
                      annotation_text=e.name, annotation_position="top left", annotation=dict(font=dict(size=11, color=e.color)))
    for ev in ctx.events:
        y, mth = (int(x) for x in ev["month"].split("-")[:2])
        fig.add_vline(x=dt.date(y, mth, 1), line_width=2, line_color=ev["color"], opacity=0.9,
                      annotation_text=ev["label"] or None, annotation_position="top right",
                      annotation=dict(font=dict(size=11, color=ev["color"])))
    lo = min(ed["date"].min(), _batch_date(ctx.meta.iloc[0]["batch"]))
    hi = max(ed["date"].max(), _batch_date(ctx.meta.iloc[-1]["batch"])) + dt.timedelta(days=120)
    CH.style(fig, height=360, y_title="requests", legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(range=[lo, hi], showgrid=False)
    st.plotly_chart(fig, key="rfs_fig1", width="stretch")
    st.caption("Bars: RFS editions by first-seen date (essays amber, consolidated page versions blue, seasonal editions orange). "
               "Era bands use the batch start months (Winter Jan, Spring Apr, Summer Jun, Fall Sep).")

    st.subheader("Browse requests")
    req = ctx.tables["rfs_requests"]
    labels = ed.sort_values("edition_order", ascending=False)["edition_label"].tolist()
    pick = st.selectbox("Edition", labels, key="rfs_ed")
    sub = req[req["edition_label"] == pick]
    st.caption(f"{len(sub)} requests · era: {sub['era'].iloc[0] if len(sub) else ''}")
    for _, r in sub.iterrows():
        partner = f" — {r['partner']}" if isinstance(r["partner"], str) and r["partner"] else ""
        with st.expander(f"{r['title']}{partner}"):
            st.write(r["body_text"])
            st.caption(f"source: {r['source_url']}")
    download(req, "rfs_requests.csv")

    st.subheader("YC labels mentioned in RFS text (string match)")
    st.caption("Case-insensitive whole-word match of every YC tag / industry / subindustry name against request title and body. "
               "A mention is not a classification of the request.")
    men = ctx.tables["rfs_mentions"]
    lt = st.radio("Label type", sorted(men["label_type"].unique()), horizontal=True, key="rfs_lt")
    m = men[men["label_type"] == lt]
    wide = m.pivot_table(index="label", columns="edition_label", values="requests_mentioning", aggfunc="sum").fillna(0)
    order = ed.sort_values("edition_order")["edition_label"].tolist()
    wide = wide[[c for c in order if c in wide.columns]]
    wide = wide.loc[wide.sum(axis=1).sort_values(ascending=False).head(30).index]
    st.plotly_chart(CH.heatmap(wide.astype(int), value_title="requests"), key="rfs_fig2", width="stretch")
    download(men, "rfs_label_mentions.csv")
