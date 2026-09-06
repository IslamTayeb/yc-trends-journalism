"""Select earliest + first-commit-of-each-month for companies/all.json and extract them from the partial clone."""
from __future__ import annotations
import json, subprocess
from .config import RAW

def main():
    repo = RAW / "clones" / "yc-oss-api"; out = RAW / "snapshots"; out.mkdir(exist_ok=True)
    log = subprocess.run(["git", "-C", str(repo), "log", "--reverse", "--format=%H %cI", "--", "companies/all.json"], capture_output=True, text=True, check=True).stdout
    rows = [l.split() for l in log.strip().splitlines()]
    seen = {}
    for sha, d in rows: seen.setdefault(d[:7], (sha, d))
    seen["first"] = tuple(rows[0])
    commits = sorted({v[0]: v for v in seen.values()}.values(), key=lambda x: x[1])
    json.dump(commits, open(out / "snapshot_commits.json", "w"), indent=1)
    for sha, d in commits:
        f = out / f"all_{d[:10]}_{sha[:7]}.json"
        if f.exists(): continue
        f.write_bytes(subprocess.run(["git", "-C", str(repo), "show", f"{sha}:companies/all.json"], capture_output=True, check=True).stdout)
        print("extracted", f.name)

if __name__ == "__main__":
    main()
