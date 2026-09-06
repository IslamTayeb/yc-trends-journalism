#!/usr/bin/env bash
# Re-download all raw sources. Idempotent. Run from repo root.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw/clones data/raw/yc-oss-api/companies data/raw/yc-dataset data/raw/snapshots data/raw/rfs/{current,wayback,essays}
# 1. primary: yc-oss/api (history without blobs -> lets us pull historical companies/all.json)
if [ ! -d data/raw/clones/yc-oss-api/.git ]; then git clone -q --filter=blob:none https://github.com/yc-oss/api data/raw/clones/yc-oss-api; else git -C data/raw/clones/yc-oss-api pull -q; fi
S=data/raw/clones/yc-oss-api
cp $S/meta.json data/raw/yc-oss-api/; cp $S/companies/all.json data/raw/yc-oss-api/companies/
rm -rf data/raw/yc-oss-api/{batches,industries,tags}; mkdir -p data/raw/yc-oss-api/{batches,industries,tags}
cp $S/batches/*.json data/raw/yc-oss-api/batches/; cp $S/industries/*.json data/raw/yc-oss-api/industries/; cp $S/tags/*.json data/raw/yc-oss-api/tags/
cp $S/changes/latest.md data/raw/yc-oss-api/changes_latest.md; cp $S/README.md data/raw/yc-oss-api/README_upstream.md
# 2. secondary: EXTREMOPHILARUM/yc-dataset
if [ ! -d data/raw/clones/yc-dataset/.git ]; then git clone -q --depth 1 https://github.com/EXTREMOPHILARUM/yc-dataset data/raw/clones/yc-dataset; else git -C data/raw/clones/yc-dataset pull -q; fi
cp data/raw/clones/yc-dataset/data/index.json data/raw/yc-dataset/; cp data/raw/clones/yc-dataset/raw/yc_directory.json data/raw/yc-dataset/; cp data/raw/clones/yc-dataset/README.md data/raw/yc-dataset/README_upstream.md
# 3. historical snapshots of companies/all.json: earliest + first commit of each month
PYTHONPATH=src uv run python -m ycnative.snapshots
# 4. RFS pages
PYTHONPATH=src uv run python -m ycnative.rfs_fetch
