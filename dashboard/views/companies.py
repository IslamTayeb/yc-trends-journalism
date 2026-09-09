from __future__ import annotations

import streamlit as st

import context as X
from views._common import download

SHOW = ["name", "batch", "era", "industry", "subindustry", "tags", "all_locations", "status", "team_size", "one_liner",
        "yc_profile_url", "website"]


def render() -> None:
    ctx = X.get()
    st.title("Company explorer")
    df = ctx.companies
    c1, c2, c3, c4 = st.columns(4)
    eras = c1.multiselect("Era", ctx.era_names, key="ce_era")
    batches = c2.multiselect("Batch", list(ctx.meta["batch"]), key="ce_batch")
    inds = c3.multiselect("Industry", sorted(df["industry"].dropna().unique()), key="ce_ind")
    subs = c4.multiselect("Subindustry", sorted(df["subindustry"].dropna().unique()), key="ce_sub")
    c5, c6, c7, c8 = st.columns(4)
    all_tags = sorted(ctx.tags["tag"].unique())
    tags = c5.multiselect("Tags (any of)", all_tags, key="ce_tags")
    countries = c6.multiselect("Country (from regions)", sorted(set(ctx.tables["geo_countries"]["country"])), key="ce_ctry")
    status = c7.multiselect("Status", sorted(df["status"].dropna().unique()), key="ce_status")
    q = c8.text_input("Text search (name, one-liner, description)", key="ce_q").strip()

    sub = df
    if eras:
        sub = sub[sub["era"].isin(eras)]
    if batches:
        sub = sub[sub["batch"].isin(batches)]
    if inds:
        sub = sub[sub["industry"].isin(inds)]
    if subs:
        sub = sub[sub["subindustry"].isin(subs)]
    if tags:
        ids = ctx.tags.loc[ctx.tags["tag"].isin(tags), "company_id"].unique()
        sub = sub[sub["id"].isin(ids)]
    if countries:
        sub = sub[sub["n_countries"].fillna("").apply(lambda s: any(c in s.split("|") for c in countries))]
    if status:
        sub = sub[sub["status"].isin(status)]
    if q:
        ql = q.lower()
        mask = (sub["name"].fillna("").str.lower().str.contains(ql, regex=False)
                | sub["one_liner"].fillna("").str.lower().str.contains(ql, regex=False)
                | sub["long_description"].fillna("").str.lower().str.contains(ql, regex=False))
        sub = sub[mask]

    st.markdown(f"**{len(sub):,}** of {len(df):,} companies in window")
    if ctx.has_eras and len(sub):
        st.dataframe(sub.groupby("era", observed=True).size().reindex(ctx.era_names).fillna(0).astype(int).rename("companies").to_frame().T,
                     width="stretch")
    out = sub.sort_values("n_batch_order", ascending=False)[SHOW]
    st.dataframe(out, hide_index=True, width="stretch", height=560,
                 column_config={"yc_profile_url": st.column_config.LinkColumn("YC profile", display_text="open"),
                                "website": st.column_config.LinkColumn("Website", display_text="open"),
                                "tags": st.column_config.TextColumn("tags (YC)", width="large")})
    download(sub.drop(columns=["pos"]), "companies_filtered.csv")
