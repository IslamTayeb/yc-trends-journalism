"""Transparent, rule-based classification of a category's share-of-batch series.
Rules (shares in % of batch, over FULL batches only, chronological):
  early = mean share of first n_early_batches ; late = mean share of last n_late_batches
  Emerging   : late - early >= emerging_min_pp_gain AND late >= emerging_min_ratio * early AND latest count >= emerging_min_latest_count
  Declining  : early >= declining_min_early_share_pct AND late <= declining_max_ratio * early AND early - late >= declining_min_pp_loss
  Spiky      : (not Emerging/Declining) AND peak >= spiky_peak_over_median * median AND peak >= spiky_min_peak_pct
  Persistent : (none of the above) AND mean >= persistent_min_mean_pct AND coefficient of variation <= persistent_max_cv
  Otherwise  : Low-volume / mixed
"""
from __future__ import annotations
import numpy as np

def classify(shares: np.ndarray, counts: np.ndarray, p: dict) -> dict:
    s = np.asarray(shares, float); c = np.asarray(counts, float)
    if len(s) == 0:
        return {"early_share_pct": None, "late_share_pct": None, "median_share_pct": None, "cv_share": None, "emergence_class": "n/a"}
    ne, nl = int(p["n_early_batches"]), int(p["n_late_batches"])
    early, late = s[:ne].mean(), s[-nl:].mean()
    med, mean, peak = float(np.median(s)), float(s.mean()), float(s.max())
    cv = float(s.std(ddof=0) / mean) if mean > 0 else None
    cls = "Low-volume / mixed"
    if (late - early >= p["emerging_min_pp_gain"]) and (late >= p["emerging_min_ratio"] * early) and (c[-1] >= p["emerging_min_latest_count"]):
        cls = "Emerging"
    elif (early >= p["declining_min_early_share_pct"]) and (late <= p["declining_max_ratio"] * early) and (early - late >= p["declining_min_pp_loss"]):
        cls = "Declining"
    elif (peak >= p["spiky_peak_over_median"] * med) and (peak >= p["spiky_min_peak_pct"]):
        cls = "Spiky"
    elif (mean >= p["persistent_min_mean_pct"]) and (cv is not None and cv <= p["persistent_max_cv"]):
        cls = "Persistent"
    return {"early_share_pct": round(float(early), 3), "late_share_pct": round(float(late), 3),
            "median_share_pct": round(med, 3), "cv_share": round(cv, 3) if cv is not None else None, "emergence_class": cls}
