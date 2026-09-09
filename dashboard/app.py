"""YC batch composition explorer with user-defined eras.

Run:  uv run streamlit run dashboard/app.py
"""
from __future__ import annotations

import streamlit as st

import context as X
import data
import eras as E
from compute import MEASURES
from views import overview, categories, era_compare, cooccurrence, geography, diversity, companies, rfs, caveats

st.set_page_config(page_title="YC by era", page_icon="🟧", layout="wide", initial_sidebar_state="expanded")

PAGES = [
    st.Page(overview.render, title="Overview", icon="🏠", url_path="overview", default=True),
    st.Page(categories.render, title="Categories over time", icon="📈", url_path="categories"),
    st.Page(era_compare.render, title="Compare eras", icon="⚖️", url_path="compare"),
    st.Page(cooccurrence.render, title="Tag co-occurrence", icon="🔗", url_path="cooccurrence"),
    st.Page(geography.render, title="Geography", icon="🌍", url_path="geography"),
    st.Page(diversity.render, title="Concentration", icon="🎯", url_path="diversity"),
    st.Page(companies.render, title="Company explorer", icon="🔎", url_path="companies"),
    st.Page(rfs.render, title="Requests for Startups", icon="📜", url_path="rfs"),
    st.Page(caveats.render, title="Caveats & provenance", icon="⚠️", url_path="caveats"),
]


def _init_state() -> None:
    if "era_state" in st.session_state:
        return
    qp = st.query_params.get("eras")
    state = E.state_from_param(qp) if qp else None
    st.session_state["era_state"] = state or E.load_state()


def _reset_widgets() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith(("cuts_ms", "name_", "before_name_in", "years_rng")):
            del st.session_state[k]


def sidebar() -> X.Ctx:
    _init_state()
    meta_all = data.batch_meta()
    years = sorted(meta_all["year"].unique())
    with st.sidebar:
        st.markdown("### Window")
        y0, y1 = st.slider("Batch years", int(years[0]), int(years[-1]), (2021, int(years[-1])), key="years_rng",
                           help="Which batches are loaded. Everything else (eras, tables, charts) follows this window.")
        meta = data.window_meta(meta_all, y0, y1)

        st.markdown("### Eras")
        st.caption("Nothing is pre-annotated. Pick the batches where a new era *starts*; batches before the first cut form a leading era.")
        state = st.session_state["era_state"]
        opts = list(meta["batch"])
        fmt = dict(zip(meta["batch"], meta["batch_code"] + " · " + meta["batch"]))
        cuts = st.multiselect("A new era starts at", opts, default=[c for c in state["cuts"] if c in opts],
                              format_func=lambda b: fmt[b], key="cuts_ms")
        order = dict(zip(meta["batch"], meta["batch_order"]))
        cuts = sorted(cuts, key=order.get)
        names = dict(state.get("names", {}))
        before_name = state.get("before_name", "")
        if cuts:
            if cuts[0] != opts[0]:
                before_name = st.text_input(f"Era before {fmt[cuts[0]].split(' · ')[0]}", value=before_name,
                                            placeholder=f"Before {names.get(cuts[0]) or E.default_name(cuts[0], meta)}",
                                            key="before_name_in")
            for c in cuts:
                names[c] = st.text_input(f"Era starting {fmt[c]}", value=names.get(c, ""),
                                         placeholder=E.default_name(c, meta), key=f"name_{c}")
        new_state = {"cuts": cuts, "names": {k: v for k, v in names.items() if v}, "before_name": before_name}
        st.session_state["era_state"] = new_state
        st.query_params["eras"] = E.state_to_param(new_state)

        c1, c2 = st.columns(2)
        if c1.button("Save eras", width="stretch", help="Writes dashboard/eras.local.json (gitignored) so the eras come back next launch."):
            E.save_state(new_state)
            st.toast("Saved to dashboard/eras.local.json")
        if c2.button("Clear eras", width="stretch"):
            E.reset_saved()
            st.session_state["era_state"] = E.empty_state()
            _reset_widgets()
            st.query_params.clear()
            st.rerun()
        st.caption("The URL always carries the current eras, so you can bookmark or share it.")

        st.markdown("### Measure")
        measure = st.radio("Measure", list(MEASURES), format_func=MEASURES.get, key="measure",
                           label_visibility="collapsed",
                           help="Share of batch = label count / all companies in the batch. Share of tagged = / companies with at least one tag (tag views only).")
        exclude_partial = st.toggle("Exclude partial batches from era tables", value=True,
                                    help=f"Batches with fewer than {data.config()['MIN_FULL_BATCH']} companies (in progress). They stay on the time axis with hollow markers.")
        exclude_low_tag = st.toggle("Exclude low-tag-coverage batches from tag stats", value=True,
                                    help=f"Batches where more than {data.config()['TAG_COVERAGE_MAX_ZERO_TAG_PCT']}% of companies have no tags. Applies to share measures only.")

    ctx = X.build(y0, y1, new_state, measure, exclude_partial, exclude_low_tag)
    st.session_state["ctx"] = ctx
    return ctx


def main() -> None:
    pg = st.navigation(PAGES)
    ctx = sidebar()
    with st.sidebar:
        st.markdown("---")
        flags = []
        if ctx.partial_batches:
            flags.append(f"partial: {', '.join(ctx.meta.set_index('batch').loc[list(ctx.partial_batches), 'batch_code'])}")
        if ctx.low_tag_batches:
            flags.append(f"low tag coverage: {', '.join(ctx.meta.set_index('batch').loc[list(ctx.low_tag_batches), 'batch_code'])}")
        st.caption(f"{len(ctx.meta)} batches · {len(ctx.companies):,} companies · {len(ctx.eras) or 'no'} eras"
                   + ("  \n" + "  \n".join(flags) if flags else ""))
        st.caption("Labels are YC's own (industry, subindustry, tags, regions), never merged or renamed.")
    pg.run()


if __name__ == "__main__":
    main()
