"""Descriptive headquarters/location analysis from YC-native regions and all_locations fields."""
from __future__ import annotations
import pandas as pd

def geography(df: pd.DataFrame, batch_meta: pd.DataFrame):
    rows = []
    for b, g in df.groupby("batch", sort=False):
        n = len(g)
        r = {"batch": b, "total_companies": n,
             "us_companies": int(g["n_is_us"].sum()), "us_share_pct": round(100 * g["n_is_us"].mean(), 2),
             "non_us_companies": int((~g["n_is_us"]).sum()), "non_us_share_pct": round(100 * (~g["n_is_us"]).mean(), 2),
             "no_country_in_regions": int(g["n_countries"].map(len).eq(0).sum()),
             "remote_any_companies": int(g["n_is_remote"].sum()), "remote_any_share_pct": round(100 * g["n_is_remote"].mean(), 2),
             "fully_remote_companies": int((g["n_remote_kind"] == "Fully Remote").sum()),
             "partly_remote_companies": int((g["n_remote_kind"] == "Partly Remote").sum()),
             "unique_countries": int(g["n_countries"].explode().dropna().nunique()),
             "multi_country_companies": int(g["n_countries"].map(len).gt(1).sum())}
        rows.append(r)
    wide = pd.DataFrame(rows).merge(batch_meta[["batch", "batch_order", "is_partial_batch"]], on="batch").sort_values("batch_order")
    def long(col, name):
        t = df[["id", "batch"]].join(df[col].rename(name)).explode(name).dropna(subset=[name])
        c = t.drop_duplicates(["id", name]).groupby([name, "batch"]).size().rename("count").reset_index()
        c = c.merge(batch_meta[["batch", "batch_order", "total_companies"]], on="batch")
        c["share_pct"] = (100 * c["count"] / c["total_companies"]).round(2)
        return c.sort_values([name, "batch_order"]).reset_index(drop=True)
    countries = long("n_countries", "country")
    macro = long("n_macro_regions", "macro_region")
    city = df[["id", "batch", "n_city", "n_country_from_locations"]].dropna(subset=["n_city"])
    city = city.assign(city=city["n_city"] + ", " + city["n_country_from_locations"].fillna(""))
    cities = city.groupby(["city", "batch"]).size().rename("count").reset_index().merge(batch_meta[["batch", "batch_order", "total_companies"]], on="batch")
    cities["share_pct"] = (100 * cities["count"] / cities["total_companies"]).round(2)
    return wide.reset_index(drop=True), countries, macro, cities.sort_values(["city", "batch_order"]).reset_index(drop=True)
