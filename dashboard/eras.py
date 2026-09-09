"""User-defined eras.

An era set is a list of *cut points*: batches where a new era starts, plus a name per cut.
Batches in the window before the first cut form an implicit leading era. The repo ships no
annotations: dashboard/eras.json is the empty default and user edits go to
dashboard/eras.local.json (gitignored) and/or the URL query parameter `eras`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "eras.json"
LOCAL_FILE = HERE / "eras.local.json"

PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]


@dataclass
class Era:
    name: str
    start_batch: str
    end_batch: str
    start_order: int
    end_order: int
    start_pos: int
    end_pos: int
    n_batches: int
    color: str
    index: int

    def to_dict(self) -> dict:
        return asdict(self)


def empty_state() -> dict:
    return {"cuts": [], "names": {}, "before_name": ""}


def load_state() -> dict:
    for path in (LOCAL_FILE, DEFAULT_FILE):
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                return {**empty_state(), **raw}
            except json.JSONDecodeError:
                continue
    return empty_state()


def save_state(state: dict) -> Path:
    LOCAL_FILE.write_text(json.dumps(state, indent=1))
    return LOCAL_FILE


def reset_saved() -> None:
    if LOCAL_FILE.exists():
        LOCAL_FILE.unlink()


def state_to_param(state: dict) -> str:
    return json.dumps({"cuts": state["cuts"], "names": state["names"], "before_name": state.get("before_name", "")},
                      separators=(",", ":"))


def state_from_param(s: str) -> dict | None:
    try:
        raw = json.loads(s)
        if not isinstance(raw, dict) or not isinstance(raw.get("cuts", []), list):
            return None
        return {**empty_state(), **raw}
    except (json.JSONDecodeError, TypeError):
        return None


def default_name(batch: str, meta: pd.DataFrame) -> str:
    code = meta.loc[meta["batch"] == batch, "batch_code"]
    return f"From {code.iloc[0]}" if len(code) else f"From {batch}"


def build_eras(state: dict, meta: pd.DataFrame) -> list[Era]:
    """Turn cut points into contiguous eras over the batches in `meta` (already windowed).

    Cuts outside the window are ignored. Returns [] when there are no cuts inside the window.
    """
    if meta.empty:
        return []
    order = dict(zip(meta["batch"], meta["batch_order"]))
    pos = dict(zip(meta["batch"], meta["pos"]))
    cuts = sorted({c for c in state.get("cuts", []) if c in order}, key=order.get)
    if not cuts:
        return []
    names = state.get("names", {})
    first_batch = meta.iloc[0]["batch"]
    starts: list[tuple[str, str]] = []
    if cuts[0] != first_batch:
        before = state.get("before_name") or f"Before {names.get(cuts[0]) or default_name(cuts[0], meta)}"
        starts.append((before, first_batch))
    for c in cuts:
        starts.append((names.get(c) or default_name(c, meta), c))
    eras: list[Era] = []
    batches = list(meta["batch"])
    for i, (name, start) in enumerate(starts):
        end = batches[pos[starts[i + 1][1]] - 1] if i + 1 < len(starts) else batches[-1]
        eras.append(Era(
            name=name, start_batch=start, end_batch=end,
            start_order=int(order[start]), end_order=int(order[end]),
            start_pos=int(pos[start]), end_pos=int(pos[end]),
            n_batches=int(pos[end] - pos[start] + 1),
            color=PAL[i % len(PAL)], index=i,
        ))
    return eras


def assign_era(batch_order: pd.Series, eras: list[Era]) -> pd.Series:
    """Map a batch_order series to era names (NaN outside every era). No eras -> 'All'."""
    if not eras:
        return pd.Series("All", index=batch_order.index, dtype="object")
    bins = [e.start_order - 0.5 for e in eras] + [eras[-1].end_order + 0.5]
    labels = [e.name for e in eras]
    return pd.cut(batch_order.astype(float), bins=bins, labels=labels, ordered=False).astype("object")


def era_names(eras: list[Era]) -> list[str]:
    return [e.name for e in eras] if eras else ["All"]


def era_color_map(eras: list[Era]) -> dict[str, str]:
    return {e.name: e.color for e in eras} if eras else {"All": PAL[0]}
