"""Builds the per-run context (windowed tables with an `era` column) shared by every view."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

import data
import eras as E


@dataclass
class Ctx:
    cfg: dict
    prov: dict
    meta: pd.DataFrame            # batches in window, chronological, with era
    eras: list[E.Era]
    era_names: list[str]
    colors: dict[str, str]
    companies: pd.DataFrame       # windowed, with era
    tags: pd.DataFrame            # long, windowed, with era/pos/flags
    industries: pd.DataFrame
    subindustries: pd.DataFrame
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    measure: str = "share"        # share | tagged | count
    exclude_partial: bool = True
    exclude_low_tag: bool = True
    state: dict = field(default_factory=E.empty_state)
    start_year: int = 2021
    end_year: int | None = None

    # ---- helpers used by views -------------------------------------------------
    @property
    def has_eras(self) -> bool:
        return bool(self.eras)

    @property
    def partial_batches(self) -> tuple[str, ...]:
        return tuple(self.meta.loc[self.meta["is_partial_batch"], "batch"])

    @property
    def low_tag_batches(self) -> tuple[str, ...]:
        return tuple(self.meta.loc[self.meta["low_tag_coverage"], "batch"])

    def excluded(self, tag_based: bool = False) -> tuple[str, ...]:
        out: set[str] = set()
        if self.exclude_partial:
            out |= set(self.partial_batches)
        if tag_based and self.exclude_low_tag and self.measure != "count":
            out |= set(self.low_tag_batches)
        return tuple(sorted(out, key=lambda b: self.meta.set_index("batch").loc[b, "batch_order"]))

    @property
    def plot_meta(self) -> pd.DataFrame:
        """Batches drawn on time-axis charts: those with at least MIN_PLOT_BATCH companies (tables keep all)."""
        return self.meta[self.meta["total_companies"] >= int(self.cfg.get("MIN_PLOT_BATCH", 5))]

    def value_col(self) -> str:
        return "count" if self.measure == "count" else "share_pct"

    def measure_label(self) -> str:
        from compute import MEASURES
        return MEASURES[self.measure]

    def long(self, label_type: str) -> tuple[pd.DataFrame, str]:
        return {"industry": (self.industries[self.industries["level"] == "top"], "industry"),
                "subindustry": (self.subindustries, "subindustry"),
                "tag": (self.tags, "tag")}[label_type]

    def with_era(self, df: pd.DataFrame) -> pd.DataFrame:
        """Attach batch position/flags and era to any batch-level table."""
        d = data.attach_batch(df, self.meta)
        d["era"] = E.assign_era(d["batch_order"], self.eras)
        return d


def build(start_year: int, end_year: int | None, state: dict, measure: str,
          exclude_partial: bool, exclude_low_tag: bool) -> Ctx:
    tables = data.load_all()
    meta = data.window_meta(data.batch_meta(), start_year, end_year)
    era_list = E.build_eras(state, meta)
    meta = meta.copy()
    meta["era"] = E.assign_era(meta["batch_order"], era_list)

    comp = tables["companies"]
    comp = comp[comp["batch"].isin(meta["batch"])].copy()
    comp["era"] = E.assign_era(comp["n_batch_order"], era_list)
    comp["pos"] = comp["batch"].map(meta.set_index("batch")["pos"])

    def prep(t: pd.DataFrame) -> pd.DataFrame:
        d = data.attach_batch(t, meta)
        d["era"] = E.assign_era(d["batch_order"], era_list)
        return d

    return Ctx(
        cfg=data.config(), prov=data.provenance(), meta=meta, eras=era_list,
        era_names=E.era_names(era_list), colors=E.era_color_map(era_list),
        companies=comp, tags=prep(tables["tags"]), industries=prep(tables["industries"]),
        subindustries=prep(tables["subindustries"]), tables=tables, measure=measure,
        exclude_partial=exclude_partial, exclude_low_tag=exclude_low_tag, state=state,
        start_year=start_year, end_year=end_year,
    )


def get() -> Ctx:
    return st.session_state["ctx"]
