"""Download one Wayback snapshot of ycombinator.com/rfs per month (2014-07 .. now)."""
import json, time, urllib.request, pathlib, sys
cdx = json.load(open('wayback/cdx_rfs.json'))[1:]
by_month = {}
for ts, sc, ln, dg in cdx:
    by_month.setdefault(ts[:6], ts)   # first snapshot of each month
out = pathlib.Path('wayback/html'); out.mkdir(exist_ok=True)
log = []
for month, ts in sorted(by_month.items()):
    f = out / f'{ts}.html'
    if f.exists() and f.stat().st_size > 1000:
        continue
    url = f'http://web.archive.org/web/{ts}id_/https://www.ycombinator.com/rfs'
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research; yc-trends)'})
            data = urllib.request.urlopen(req, timeout=60).read()
            f.write_bytes(data); log.append((ts, len(data), 'ok')); break
        except Exception as e:
            log.append((ts, 0, f'err{attempt}:{e}')); time.sleep(5 * (attempt + 1))
    time.sleep(1.5)
json.dump(log, open('wayback/fetch_log.json', 'w'), indent=1)
print('months', len(by_month), 'ok', sum(1 for l in log if l[2] == 'ok'), 'files', len(list(out.glob('*.html'))))
