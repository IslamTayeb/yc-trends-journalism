"""Parse YC Requests for Startups (RFS) pages into a deterministic request-level table, then string-match
YC-native labels against request text. No semantic interpretation.

Eras:
  essays       2009-2013  ycombinator.com/rfsN.html  (one request per page)
  consolidated 2014-2024  ycombinator.com/rfs        (h3 = category; page carries a "Month YYYY" date label until 2022)
  seasonal     2024-      ycombinator.com/rfs        (h2 = edition e.g. "Fall 2026"; h3 = request title; "By <partner>")
"""
from __future__ import annotations
import re, glob, hashlib, os
import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag
from .config import RAW

R = RAW / "rfs"
SKIP_HEADINGS = {"introduction", "rfs introduction", "notes", "hacker news", "startup school", "jobs", "programs", "company", "resources",
                 "make something people want.", "elsewhere", "contents", "also", "footer", "requests for startups", "about", "apply",
                 "blog", "library", "people", "companies", "y combinator"}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
SEASON_RANK = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}

def _clean(s): return re.sub(r"\s+", " ", s).strip()

def _soup(path):
    s = BeautifulSoup(open(path, errors="ignore").read(), "lxml")
    for t in s(["script", "style", "noscript", "nav", "footer", "header", "svg", "button"]): t.decompose()
    return s

def _sections(soup):
    """Walk the document in order; return list of dicts {edition(h2), title(h3), partner, body}."""
    body = soup.body or soup
    out, cur_h2, cur = [], None, None
    intro_h2 = None
    for el in body.descendants:
        if isinstance(el, Tag):
            if el.name == "h2":
                txt = _clean(el.get_text(" "))
                if re.fullmatch(r"(Winter|Spring|Summer|Fall) 20\d\d", txt):
                    cur_h2 = txt; cur = None; el["data-structural"] = "1"
                elif txt.lower() in SKIP_HEADINGS:
                    cur_h2 = None; cur = None; el["data-structural"] = "1"
                # any other h2 is a tagline inside the current section (2014-2022 layout): its strings are kept as body text
                continue
            if el.name in ("h3", "h1"):
                txt = re.sub(r"\s*(NEW)$", "", _clean(el.get_text(" ")).rstrip("#").strip())
                if el.name == "h1" or txt.lower() in SKIP_HEADINGS or not txt:
                    cur = None; continue
                cur = {"edition_h2": cur_h2, "title": txt, "partner": None, "body": []}
                out.append(cur); continue
            if el.name == "span" and cur is not None and not cur["body"] and cur["partner"] is None:
                t = _clean(el.get_text(" "))
                if t.startswith("By ") and len(t) < 160:
                    cur["partner"] = t[3:].strip(); el["data-partner"] = "1"; continue
        elif isinstance(el, NavigableString) and cur is not None:
            anc = [a for a in el.parents if isinstance(a, Tag)]
            if any(a.name in ("h1", "h3", "h4") or a.get("data-partner") or (a.name == "h2" and a.get("data-structural")) for a in anc): continue
            t = _clean(str(el))
            if t and t != "#":
                cur["body"].append(t)
    for s in out:
        s["body"] = _clean(" ".join(s["body"]))
    return out

def parse_snapshot(path, era_hint=None):
    soup = _soup(path)
    text = _clean(soup.get_text(" "))
    m = re.search(rf"({MONTHS}) (20\d\d)", text[:4000])
    date_label = m.group(0) if m else None
    secs = _sections(soup)
    return date_label, secs

def _edition_order(label):
    m = re.fullmatch(r"(Winter|Spring|Summer|Fall) (20\d\d)", label or "")
    if m: return int(m.group(2)) * 10 + SEASON_RANK[m.group(1)]
    m = re.fullmatch(rf"({MONTHS}) (20\d\d)", label or "")
    if m:
        mo = [x for x in MONTHS.split("|")].index(m.group(1)) + 1
        return int(m.group(2)) * 10 + (0 if mo <= 3 else 1 if mo <= 6 else 2 if mo <= 9 else 3)
    return None

def build():
    rows = []
    # essays
    for f in sorted(glob.glob(str(R / "essays" / "rfs*.html"))):
        n = int(re.search(r"rfs(\d+)_", os.path.basename(f)).group(1)); ts = re.search(r"_(\d{14})", f).group(1)
        soup = _soup(f); title = _clean((soup.title.get_text() if soup.title else "") or "")
        title = re.sub(r"^YC\s*RFS\s*\d+:\s*", "", title, flags=re.I) or f"RFS {n}"
        body = _clean(soup.get_text(" "))
        rows.append({"era": "essays", "edition_label": f"RFS {n}", "edition_date_hint": ts[:4], "edition_order": int(ts[:4]) * 10,
                     "snapshot": ts, "title": title, "partner": None, "body_text": body, "source_url": f"https://web.archive.org/web/{ts}/http://ycombinator.com/rfs{n}.html"})
    # wayback consolidated/seasonal + current page
    snaps = sorted(glob.glob(str(R / "wayback" / "html" / "*.html")))
    cur = sorted(glob.glob(str(R / "current" / "*.html")))
    undated_versions = {}
    for f in snaps + cur:
        ts = re.search(r"(\d{14})", os.path.basename(f)); ts = ts.group(1) if ts else re.search(r"(\d{8})T", os.path.basename(f)).group(1) + "000000"
        if os.path.getsize(f) < 2000: continue
        date_label, secs = parse_snapshot(f)
        if not secs: continue
        for s in secs:
            if s["edition_h2"]:
                era, label = "seasonal", s["edition_h2"]
            elif date_label:
                era, label = "consolidated", date_label
            else:
                # undated consolidated version: identify by the set of titles in this snapshot
                key = hashlib.sha1("|".join(sorted(x["title"] for x in secs)).encode()).hexdigest()[:8]
                label = undated_versions.setdefault(key, f"undated version first captured {ts[:4]}-{ts[4:6]}-{ts[6:8]}")
                era = "consolidated"
            src = f"https://web.archive.org/web/{ts}/https://www.ycombinator.com/rfs" if "wayback" in f else "https://www.ycombinator.com/rfs"
            rows.append({"era": era, "edition_label": label, "edition_date_hint": ts[:8], "edition_order": _edition_order(label) or int(ts[:4]) * 10 + (int(ts[4:6]) - 1) // 3,
                         "snapshot": ts, "title": s["title"], "partner": s["partner"], "body_text": s["body"], "source_url": src})
    df = pd.DataFrame(rows)
    seasonal_sets = {lab: set(g["title"]) for lab, g in df[df.era == "seasonal"].groupby("edition_label")}
    for lab, g in df[df.edition_label.str.startswith("undated version")].groupby("edition_label"):
        titles = set(g["title"])
        for slab, sset in seasonal_sets.items():
            if len(titles & sset) / max(len(titles | sset), 1) >= 0.9:
                df.loc[df.edition_label == lab, ["edition_label", "era", "edition_order"]] = [slab, "seasonal", _edition_order(slab)]
    df["body_hash"] = df["body_text"].map(lambda t: hashlib.sha1(t.encode()).hexdigest()[:10])
    # collapse to one row per (era, edition, title); keep longest body, first/last snapshot
    g = df.sort_values("snapshot").groupby(["era", "edition_label", "title"], sort=False)
    req = g.agg(edition_order=("edition_order", "min"), first_seen_snapshot=("snapshot", "min"), last_seen_snapshot=("snapshot", "max"),
                n_snapshots=("snapshot", "nunique"), partner=("partner", lambda x: next((p for p in x if p), None)),
                body_text=("body_text", lambda x: max(x, key=len)), n_body_versions=("body_hash", "nunique"), source_url=("source_url", "first")).reset_index()
    req["body_chars"] = req["body_text"].str.len()
    req = req.sort_values(["edition_order", "first_seen_snapshot", "title"]).reset_index(drop=True)
    # title persistence across consolidated versions
    ed = req.groupby(["era", "edition_label"]).agg(edition_order=("edition_order", "min"), n_requests=("title", "size"),
                                                   first_seen=("first_seen_snapshot", "min"), last_seen=("last_seen_snapshot", "max"),
                                                   partners_named=("partner", lambda x: int(x.notna().sum()))).reset_index().sort_values(["edition_order", "first_seen"])
    persist = (req[req.era != "essays"].groupby("title").agg(n_editions=("edition_label", "nunique"), first_edition=("edition_label", "first"),
                                                            last_edition=("edition_label", "last"), first_seen=("first_seen_snapshot", "min"), last_seen=("last_seen_snapshot", "max"))
               .reset_index().sort_values(["n_editions", "first_seen"], ascending=[False, True]))
    return req, ed, persist

def label_mentions(req: pd.DataFrame, labels: dict[str, list[str]]):
    """labels: {"tag": [...], "industry": [...], "subindustry_child": [...]} exact, case-insensitive, word-boundary matches."""
    rows = []
    for kind, labs in labels.items():
        for lab in labs:
            if not lab or len(lab) < 2 or lab == "Unspecified": continue
            pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(lab) + r"(?![A-Za-z0-9])", re.I)
            for _, r in req.iterrows():
                txt = f"{r['title']} {r['body_text']}"
                n = len(pat.findall(txt))
                if n:
                    rows.append({"label_type": kind, "label": lab, "era": r["era"], "edition_label": r["edition_label"], "edition_order": r["edition_order"],
                                 "request_title": r["title"], "mentions": n, "in_title": bool(pat.search(r["title"]))})
    m = pd.DataFrame(rows)
    per_edition = (m.groupby(["label_type", "label", "era", "edition_label", "edition_order"]).agg(requests_mentioning=("request_title", "nunique"), mentions=("mentions", "sum"), in_title_any=("in_title", "max"))
                   .reset_index().sort_values(["label_type", "label", "edition_order"])) if not m.empty else m
    return m, per_edition

def before_after(per_ed: pd.DataFrame, results: dict, bmeta: pd.DataFrame, low_tag_batches: list[str], k: int = 2) -> pd.DataFrame:
    """For each (label, edition) mention: label's share in the k full batches before the edition and the k full batches
    from the edition onward (by batch order). Descriptive only; editions outside the analysis window get NaN."""
    if per_ed.empty: return per_ed
    bm = bmeta[~bmeta["is_partial_batch"]].sort_values("batch_order")
    rows = []
    kind_map = {"tag": ("tag", set(low_tag_batches)), "industry": ("industry", set()), "subindustry_child": (None, set())}
    sub_shares = results["subindustry"]["shares"]
    child_to_full = {}
    for full in sub_shares.index:
        if "->" in full: child_to_full.setdefault(full.split("->")[1].strip(), []).append(full)
    for _, r in per_ed.iterrows():
        kind, excl = kind_map[r["label_type"]]
        usable = bm[~bm["batch"].isin(excl)]
        before = usable[usable["batch_order"] < r["edition_order"]].tail(k)["batch"].tolist()
        after = usable[usable["batch_order"] >= r["edition_order"]].head(k)["batch"].tolist()
        if kind:
            sh = results[kind]["shares"]
            series = sh.loc[r["label"]] if r["label"] in sh.index else None
        else:
            fulls = child_to_full.get(r["label"], [])
            series = sub_shares.loc[fulls].sum() if fulls else None
        def mean_of(bs):
            return round(float(series[bs].mean()), 3) if (series is not None and bs) else None
        rows.append({**r.to_dict(), "batches_before": "|".join(before), "share_before_pct": mean_of(before),
                     "batches_after": "|".join(after), "share_after_pct": mean_of(after)})
    out = pd.DataFrame(rows)
    out["pp_change_after_minus_before"] = (out["share_after_pct"] - out["share_before_pct"]).round(3)
    return out
