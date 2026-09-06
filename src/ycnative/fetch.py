"""Provenance + manifest of raw files (the actual download/clone steps are in scripts/fetch_sources.sh)."""
from __future__ import annotations
import hashlib, json, subprocess, datetime as dt, pathlib
from .config import RAW, ROOT

def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def git_head(path: pathlib.Path):
    try:
        sha = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        date = subprocess.run(["git", "-C", str(path), "log", "-1", "--format=%cI"], capture_output=True, text=True, check=True).stdout.strip()
        return sha, date
    except Exception:
        return None, None

def write_provenance() -> dict:
    meta = json.load(open(RAW / "yc-oss-api" / "meta.json"))
    sha1, d1 = git_head(RAW / "clones" / "yc-oss-api")
    sha2, d2 = git_head(RAW / "clones" / "yc-dataset")
    files = {}
    for p in sorted((RAW / "yc-oss-api").rglob("*.json")) + sorted((RAW / "yc-dataset").glob("*.json")) + sorted((RAW / "snapshots").glob("*.json")):
        files[str(p.relative_to(ROOT))] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    prov = {
        "retrieval_date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "primary_source": {"repo": "https://github.com/yc-oss/api", "commit_sha": sha1, "commit_date": d1,
                            "meta_last_updated": meta.get("last_updated"), "companies_in_all_json": len(json.load(open(RAW / "yc-oss-api" / "companies" / "all.json"))),
                            "note": "Publicly launched companies with YC directory profiles (Algolia index YCCompany_By_Launch_Date_production); not every company ever accepted into YC."},
        "secondary_source": {"repo": "https://github.com/EXTREMOPHILARUM/yc-dataset", "commit_sha": sha2, "commit_date": d2,
                              "companies_in_yc_directory_json": len(json.load(open(RAW / "yc-dataset" / "yc_directory.json"))) if (RAW / "yc-dataset" / "yc_directory.json").exists() else None,
                              "usage": "enrichment / cross-check only"},
        "historical_snapshots": json.load(open(RAW / "snapshots" / "snapshot_commits.json")),
        "rfs_sources": {"current_page": "https://www.ycombinator.com/rfs", "wayback_cdx": "http://web.archive.org/cdx/search/cdx?url=ycombinator.com/rfs",
                         "essays": "ycombinator.com/rfs1.html .. rfs10.html via Wayback"},
    }
    json.dump(prov, open(ROOT / "data" / "provenance.json", "w"), indent=1)
    json.dump(files, open(RAW / "file_manifest.json", "w"), indent=1)
    return prov
