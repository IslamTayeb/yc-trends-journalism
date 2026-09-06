"""Configuration: config.yaml with environment overrides (START_YEAR, END_YEAR, OUT_DIR, FIG_DIR)."""
from __future__ import annotations
import os, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

def load_config() -> dict:
    cfg = yaml.safe_load(open(ROOT / "config.yaml"))
    for k in ("START_YEAR", "END_YEAR", "OUT_DIR", "FIG_DIR", "MIN_FULL_BATCH"):
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    cfg["START_YEAR"] = int(cfg["START_YEAR"])
    cfg["END_YEAR"] = None if str(cfg["END_YEAR"]).lower() == "latest" else int(cfg["END_YEAR"])
    cfg["MIN_FULL_BATCH"] = int(cfg["MIN_FULL_BATCH"])
    cfg["OUT"] = ROOT / cfg["OUT_DIR"]
    cfg["FIG"] = ROOT / cfg["FIG_DIR"]
    cfg["OUT"].mkdir(parents=True, exist_ok=True)
    cfg["FIG"].mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "quality").mkdir(parents=True, exist_ok=True)
    return cfg
