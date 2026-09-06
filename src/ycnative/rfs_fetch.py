"""Download Requests-for-Startups sources with plain HTTP (no browser):
  1. current https://www.ycombinator.com/rfs
  2. Wayback: first snapshot of every month of ycombinator.com/rfs (2014-07 .. now), plus extra snapshots for months whose first capture is broken
  3. Wayback: numbered essays ycombinator.com/rfs1.html .. rfs10.html (2009-2013)
Raw HTML is kept locally under data/raw/rfs/ (gitignored); parsed text is what gets committed."""
from __future__ import annotations
import json, time, datetime as dt, re, gzip, urllib.request, pathlib
from .config import RAW

UA = {"User-Agent": "Mozilla/5.0 (research; yc-trends-journalism)"}
R = RAW / "rfs"

def get(url, timeout=60, tries=4):
    """HTTP GET; transparently gunzips bodies that Wayback's id_ mode returns still compressed."""
    for i in range(tries):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
            return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
        except Exception as e:
            err = e; time.sleep(4 * (i + 1))
    raise err

def cdx(url_pattern, extra=""):
    u = f"http://web.archive.org/cdx/search/cdx?url={url_pattern}&output=json&fl=timestamp,statuscode,length,digest&filter=statuscode:200{extra}"
    return json.loads(get(u))[1:]

def fetch_current():
    d = R / "current"; d.mkdir(parents=True, exist_ok=True)
    f = d / f"rfs_{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}.html"
    f.write_bytes(get("https://www.ycombinator.com/rfs")); return f

def fetch_wayback(min_ok_bytes=5000):
    d = R / "wayback"; (d / "html").mkdir(parents=True, exist_ok=True)
    rows = cdx("ycombinator.com/rfs", "&from=20140101")
    json.dump([["timestamp", "statuscode", "length", "digest"]] + rows, open(d / "cdx_rfs.json", "w"))
    by_month = {}
    for ts, sc, ln, dg in rows: by_month.setdefault(ts[:6], []).append(ts)
    log = []
    for month, tss in sorted(by_month.items()):
        got = False
        for ts in tss[:4]:  # first capture of the month; fall back to the next captures if the page is broken/tiny
            f = d / "html" / f"{ts}.html"
            if f.exists() and f.stat().st_size >= min_ok_bytes: got = True; break
            try:
                data = get(f"http://web.archive.org/web/{ts}id_/https://www.ycombinator.com/rfs")
                f.write_bytes(data); log.append((ts, len(data)))
                if len(data) >= min_ok_bytes: got = True; break
            except Exception as e:
                log.append((ts, f"err {e}"))
            time.sleep(1.5)
        if not got: log.append((month, "no usable capture"))
    json.dump(log, open(d / "fetch_log.json", "w"), indent=1)

def fetch_essays():
    d = R / "essays"; d.mkdir(parents=True, exist_ok=True)
    rows = json.loads(get("http://web.archive.org/cdx/search/cdx?url=ycombinator.com/rfs*&output=json&fl=original,timestamp,statuscode&filter=statuscode:200&collapse=urlkey"))[1:]
    es = [r for r in rows if re.search(r"/rfs\d+\.html", r[0])]
    json.dump(es, open(d / "essay_urls.json", "w"))
    for orig, ts, sc in es:
        n = int(re.search(r"rfs(\d+)\.html", orig).group(1))
        f = d / f"rfs{n:02d}_{ts}.html"
        if f.exists(): continue
        f.write_bytes(get(f"http://web.archive.org/web/{ts}id_/{orig}")); time.sleep(1)

def main():
    print("current:", fetch_current()); fetch_wayback(); fetch_essays(); print("rfs fetch done")

if __name__ == "__main__":
    main()
