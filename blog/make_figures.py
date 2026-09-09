"""Op-ed figures, styled to imt.sh, written as self-contained SVG.

    uv run python blog/make_figures.py            # CSVs + SVGs + preview.html + PNG/PDF via headless Chrome
    uv run python blog/make_figures.py --no-raster
    uv run python blog/make_figures.py --embed-fonts   # base64 Open Sans inside the SVGs (bigger, portable)

Colours are CSS custom properties with fallbacks, so the same SVG picks up the site's tokens when inlined on
imt.sh (light and dark) and still renders on its own, following prefers-color-scheme.
"""
import argparse, base64, re, shutil, subprocess
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLOG, DATA, FIG, FONTS = (ROOT / "blog" / d for d in ("", "data", "figures", "fonts"))
PROC, GT = ROOT / "data/all_years/processed", ROOT / "data/raw/google_trends"
SEASON_MONTH = {"Winter": 1, "Spring": 4, "Summer": 6, "Fall": 9}
START, CUT, END = 20190, 20230, 20263          # W19 .. F26, second trend segment starts at W23
MIN_PLOT_BATCH, MIN_FULL_BATCH = 5, 50         # same thresholds as config.yaml
HI = {"B2B": "b", "Industrials": "o"}          # highlighted series -> roy token
GRAY = ["Healthcare", "Fintech", "Consumer", "Real Estate and Construction", "Education", "Government"]
SEC = {"Fintech": "r2", "Healthcare": "y2"}    # next two largest labels: darkened, desaturated red and yellow
SEC_HEX = {"r2": "#a3555a", "y2": "#a8893a"}
NEUTRAL = ["Consumer", "Real Estate and Construction", "Education", "Government"]   # desaturated hues away from ROYB
NEUTRAL_HEX = ("#3f8c86", "#7a68a8", "#5f9a55", "#a8627a")   # teal, violet, green, rose; muted next to ROYB, mid lightness for both grounds
MUTED_CSS = ("".join(f".imt .d{i}{{stroke:{c}}}.imt .dt{i}{{fill:{c}}}" for i, c in enumerate(NEUTRAL_HEX))
             + "".join(f".imt .s-{k}{{stroke:{c}}}.imt .f-{k}{{fill:{c}}}" for k, c in SEC_HEX.items()))


def style(name):
    """(stroke class, fill class, width) for a non-highlighted series."""
    if name in SEC: return f"s-{SEC[name]}", f"f-{SEC[name]}", 1.7
    i = NEUTRAL.index(name)
    return f"d{i}", f"dt{i}", 1.4
SHORT = {"Real Estate and Construction": "Real Estate & Constr."}
SOURCE_YC = "Source: YC company directory via github.com/yc-oss/api, snapshot 2026-09-06."
SOURCE_GT = "Source: Google Trends, worldwide web search, monthly, retrieved 2026-09-09."
CREDIT = "Chart: Islam Tayeb · imt.sh"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace'


# ---------------------------------------------------------------- data
def yc_rows():
    t = pd.read_csv(PROC / "yc_industry_trends.csv")
    t = t[(t.batch_order >= START) & (t.batch_order <= END) & (t.total_companies >= MIN_PLOT_BATCH)].copy()
    order = sorted(t.batch_order.unique())
    t["pos"] = t.batch_order.map({b: i for i, b in enumerate(order)})
    t["start_month"] = t.batch.map(lambda b: f"{b.split()[1]}-{SEASON_MONTH[b.split()[0]]:02d}")
    t["segment"] = np.where(t.batch_order < CUT, "pre_w23", "w23_on")
    named = t[t.industry != "Unspecified"].sort_values(["batch_order", "count", "industry"], ascending=[True, False, True])
    named["rank"] = named.groupby("batch_order").cumcount() + 1   # count desc, ties by name (dashboard: method="first")
    t = t.merge(named[["batch_order", "industry", "rank"]], how="left")
    t["rank"] = t["rank"].astype("Int64")
    cols = ["batch_code", "batch", "batch_order", "pos", "start_month", "industry", "count", "total_companies",
            "share_pct", "is_partial_batch", "segment", "rank"]
    t = t.sort_values(["batch_order", "industry"])[cols].reset_index(drop=True)
    t.to_csv(DATA / "yc_industry_share_w19_f26.csv", index=False)
    return t


def trends_rows():
    out = None
    for term in ("ai", "llm", "gpt"):
        d = pd.read_csv(GT / f"google_trends_{term}_worldwide_monthly_2004.csv", skiprows=2)
        d.columns = ["month", term]
        d[f"{term}_lt1"] = d[term].astype(str).str.strip() == "<1"
        d[term] = d[term].astype(str).str.replace("<1", "0.5").astype(float)
        out = d if out is None else out.merge(d, on="month")
    out = out[(out.month >= "2018-09") & (out.month <= "2026-09")].reset_index(drop=True)
    out["lt1_flags"] = out[["ai_lt1", "llm_lt1", "gpt_lt1"]].apply(lambda r: ",".join(t for t, f in zip(("ai", "llm", "gpt"), r) if f), axis=1)
    out = out[["month", "ai", "llm", "gpt", "lt1_flags"]]
    out.to_csv(DATA / "google_trends_ai_llm_gpt_worldwide_2018_2026.csv", index=False)
    return out


def fit(pos, y):
    a, b = np.polyfit(np.asarray(pos, float), np.asarray(y, float), 1)
    return a, b


# ---------------------------------------------------------------- svg helpers
CSS = """
.imt{--bg:var(--background,#fafaf9);--ink:var(--foreground,#131110);--mut:var(--muted-foreground,#6b6865);
--rule:var(--border,#dfdedb);--prule:var(--page-rule,#131110);--r:var(--roy-r,#f52027);--o:var(--roy-o,#ee7b00);
--y:var(--roy-y,#ffba06);--b:var(--roy-b,#0074c9);font-family:"Open Sans",Arial,sans-serif;font-size:13px}
@media (prefers-color-scheme:dark){.imt{--bg:var(--background,#1a1a1a);--ink:var(--foreground,#fafafa);
--mut:var(--muted-foreground,#a1a1a1);--rule:var(--border,#ffffff1a);--prule:var(--page-rule,#555)}}
.dark .imt{--bg:var(--background,#1a1a1a);--ink:var(--foreground,#fafafa);--mut:var(--muted-foreground,#a1a1a1);
--rule:var(--border,#ffffff1a);--prule:var(--page-rule,#555)}
.imt text{fill:var(--ink)}.imt .m{fill:var(--mut)}.imt .mono{font-family:MONO}
.imt .kick{font-size:11px;font-weight:700;letter-spacing:.2em}.imt .h{font-size:18px;font-weight:600}
.imt .dek,.imt .cap{font-size:12px}.imt .tick{font-size:10.5px}.imt .foot{font-size:10px}.imt .lab{font-size:11px;font-weight:700}
.imt .ground{fill:var(--bg)}.imt .grid{stroke:var(--rule);opacity:.7}.imt .axis{stroke:var(--mut);opacity:.6}
.imt .ev{stroke:var(--prule);stroke-width:1;stroke-dasharray:1.5 3.5;stroke-linecap:round}
.imt .ln{fill:none;stroke-linejoin:round;stroke-linecap:round}MUTEDCSS
.imt .trend{stroke-dasharray:5 4;opacity:.8}.imt .hollow{fill:var(--bg)}
.imt .s-r{stroke:var(--r)}.imt .s-o{stroke:var(--o)}.imt .s-y{stroke:var(--y)}.imt .s-b{stroke:var(--b)}
.imt .f-r{fill:var(--r)}.imt .f-o{fill:var(--o)}.imt .f-y{fill:var(--y)}.imt .f-b{fill:var(--b)}
.imt .area{opacity:.12}
""".replace("MONO", MONO).replace("MUTEDCSS", MUTED_CSS)


def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, w, h, embed_fonts=False):
        self.w, self.h, self.parts = w, h, []
        css = CSS + (font_faces() if embed_fonts else "")
        self.parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
                          f'class="imt" role="img"><style>{css}</style><rect class="ground" width="{w}" height="{h}"/>')

    def add(self, s): self.parts.append(s)

    def text(self, x, y, s, cls="", anchor="start", extra=""):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, cls, sw=1):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" stroke-width="{sw}"/>')

    def path(self, d, cls, sw=1, title=None, extra=""):
        t = f"<title>{esc(title)}</title>" if title else ""
        self.add(f'<path d="{d}" class="{cls}" stroke-width="{sw}"{extra}>{t}</path>')

    def dot(self, x, y, r, cls, title=None):
        t = f"<title>{esc(title)}</title>" if title else ""
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="{cls}" stroke-width="1.6">{t}</circle>')

    def header(self, kicker, tok, headline, dek):
        self.text(24, 24, kicker.upper(), f"kick mono f-{tok}")
        self.text(24, 50, headline, "h")
        for i, d in enumerate(dek): self.text(24, 70 + 16 * i, d, "dek m")
        return 70 + 16 * len(dek)

    def footer(self, caption, source):
        y = self.h - 14 - 15 * len(caption)
        for i, c in enumerate(caption): self.text(24, y + 15 * i, c, "cap m")
        self.text(24, self.h - 12, source, "foot mono m")
        self.text(self.w - 24, self.h - 12, CREDIT, "foot mono m", "end")

    def write(self, path):
        path.write_text("".join(self.parts) + "</svg>\n")
        return path


def font_faces():
    faces = []
    for f, w in (("OpenSans-Regular", 400), ("OpenSans-SemiBold", 600), ("OpenSans-Bold", 700)):
        p = FONTS / f"{f}.ttf"
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            faces.append(f'@font-face{{font-family:"Open Sans";font-weight:{w};src:url(data:font/ttf;base64,{b64}) format("truetype")}}')
    return "".join(faces)


def polyline(xs, ys): return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))


def scurve(xs, ys):
    d = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for (x1, y1), (x2, y2) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        mx = (x1 + x2) / 2
        d.append(f"C{mx:.1f},{y1:.1f} {mx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}")
    return " ".join(d)


def spread(ys, gap, lo, hi):
    """Nudge label y positions apart (min distance gap) inside [lo, hi], keeping their order."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = [ys[i] for i in order]
    for k in range(1, len(out)): out[k] = max(out[k], out[k - 1] + gap)
    out[-1] = min(out[-1], hi)
    for k in range(len(out) - 2, -1, -1): out[k] = min(out[k], out[k + 1] - gap)
    out[0] = max(out[0], lo)
    res = [0] * len(ys)
    for k, i in enumerate(order): res[i] = out[k]
    return res


def month_pos(t, start_code, end_code, month):
    """x position of a YYYY-MM between two batches, interpolating by month (a batch sits at its start month)."""
    a, b = (t[t.batch_code == c].iloc[0] for c in (start_code, end_code))
    m = lambda s: int(s[:4]) * 12 + int(s[5:])
    return a.pos + (m(month) - m(a.start_month)) / (m(b.start_month) - m(a.start_month)) * (b.pos - a.pos)


# ---------------------------------------------------------------- figure 1: share lines
def fig_share(t, embed):
    W, H = 800, 450
    s = Svg(W, H, embed)
    top = s.header("§ Fig 1  ·  YC batch composition", "r",
                   "B2B peaked at 69% of a YC batch in 2023. Industrials has tripled since 2019.",
                   ["Share of each batch's companies carrying YC's top-level industry label, Winter 2019 to Fall 2026."])
    x0, x1, y0, y1 = 52, W - 150, top + 26, H - 88
    batches = t.drop_duplicates("batch_code").sort_values("pos")
    npos = len(batches)
    X = lambda p: x0 + p / (npos - 1) * (x1 - x0)
    Y = lambda v: y1 - v / 75 * (y1 - y0)
    for v in (0, 25, 50, 75):
        s.line(x0, Y(v), x1, Y(v), "grid" if v else "axis")
        s.text(x0 - 8, Y(v) + 3.5, f"{v}%" if v else "0", "tick mono m", "end")
    for _, b in batches.iterrows():
        s.text(X(b.pos), y1 + 15, b.batch_code, "tick mono m", "middle")
    # ChatGPT rule, same cut as the trend segments
    pcut = month_pos(t, "S22", "W23", "2022-11")
    xe = X(pcut)
    s.line(xe, y0 - 6, xe, y1, "ev")
    s.text(xe + 5, y0 + 4, "ChatGPT · Nov 2022", "tick mono")
    series = lambda name: t[t.industry == name].sort_values("pos")
    for name in GRAY:
        d = series(name)
        sc, _, w = style(name)
        s.path(polyline([X(p) for p in d.pos], [Y(v) for v in d.share_pct]), f"ln {sc}", w, title=name, extra=' opacity=".9"')
    for name, tok in HI.items():
        d = series(name)
        for seg in ("pre_w23", "w23_on"):
            dd = d[d.segment == seg]
            solid = dd[~dd.is_partial_batch]
            a, b = fit(solid.pos, solid.share_pct)
            p0, p1 = (dd.pos.min(), pcut) if seg == "pre_w23" else (pcut, dd.pos.max())   # fits meet at the rule
            s.path(polyline([X(p0), X(p1)], [Y(a * p0 + b), Y(a * p1 + b)]), f"ln trend s-{tok}", 1.5,
                   title=f"{name}, least-squares fit {solid.batch_code.iloc[0]}–{solid.batch_code.iloc[-1]}: {a:+.2f} pp per batch")
            pm = (p0 + p1) / 2    # slope label on each dashed segment: above for Industrials, below for B2B
            dy = -9 if name == "Industrials" else 19
            s.text(X(pm), Y(a * pm + b) + dy, f"{a:+.1f} pp/batch", f"tick mono f-{tok}", "middle")
        s.path(polyline([X(p) for p in d.pos], [Y(v) for v in d.share_pct]), f"ln s-{tok}", 2.25)
        for _, r in d.iterrows():
            s.dot(X(r.pos), Y(r.share_pct), 3.6, f"s-{tok} {'hollow' if r.is_partial_batch else f'f-{tok}'}",
                  f"{r.batch_code} · {name} · {r.share_pct:.1f}% ({r['count']} of {r.total_companies})")
    # direct labels at the right edge, nudged apart, with a leader where a label had to move
    names = list(HI) + GRAY
    ends = [Y(series(n).iloc[-1].share_pct) for n in names]
    lys = spread(ends, 13, y0, y1)
    for name, ye, yl in zip(names, ends, lys):
        tok = HI.get(name)
        if abs(yl - ye) > 2:
            s.line(X(npos - 1) + 5, ye, X(npos - 1) + 13, yl, f"s-{tok}" if tok else style(name)[0], 0.8)
        s.text(X(npos - 1) + 16, yl + 3.5, SHORT.get(name, name), f"lab f-{tok}" if tok else f"tick {style(name)[1]}")
    s.footer(["Hollow marker: batch under 50 companies, excluded from the dashed least-squares fits (W19 to S22 and W23 to S26).",
              "A company can carry more than one industry label. Unspecified (0 companies in this window) not shown."], SOURCE_YC)
    return s.write(FIG / "yc_b2b_vs_industrials.svg")


# ---------------------------------------------------------------- figure 2: rank bump chart
def fig_rank(t, embed):
    W, H = 800, 420
    s = Svg(W, H, embed)
    top = s.header("§ Fig 2  ·  Industry rank per batch", "o",
                   "Industrials went from YC's fifth-largest industry label to its second",
                   ["Rank of the eight top-level industry labels by number of companies within each batch, Winter 2019 to Fall 2026."])
    x0, x1, y0, y1 = 196, W - 166, top + 36, H - 78
    named = t[t.industry != "Unspecified"]
    batches = named.drop_duplicates("batch_code").sort_values("pos")
    npos = len(batches)
    X = lambda p: x0 + p / (npos - 1) * (x1 - x0)
    Y = lambda r: y0 + (r - 1) / 7 * (y1 - y0)
    for r in range(1, 9):
        s.line(x0, Y(r), x1, Y(r), "grid")
        s.text(x0 - 14, Y(r) + 3.5, str(r), "tick mono m", "end")
    for _, b in batches.iterrows():   # year labels at each year's first (Winter) batch
        if b.start_month.endswith("-01"):
            s.line(X(b.pos), y1 + 4, X(b.pos), y1 + 9, "axis")
            s.text(X(b.pos), y1 + 21, b.start_month[:4], "tick mono m", "middle")
    xe = X(month_pos(t, "S22", "W23", "2022-11"))
    s.line(xe, y0 - 24, xe, y1 + 4, "ev")
    s.text(xe + 5, y0 - 16, "ChatGPT · Nov 2022", "tick mono")
    first, last = batches.iloc[0].batch, batches.iloc[-1].batch
    for name in GRAY + list(HI):
        d = named[named.industry == name].sort_values("pos")
        tok = HI.get(name)
        xs, ys = [X(p) for p in d.pos], [Y(r) for r in d["rank"]]
        if tok:
            s.path(scurve(xs, ys), f"ln s-{tok}", 3)
            for _, r in d.iterrows():
                s.dot(X(r.pos), Y(r["rank"]), 4.2, f"s-{tok} {'hollow' if r.is_partial_batch else f'f-{tok}'}",
                      f"{r.batch_code} · {name} · rank {r['rank']} ({r['count']} companies)")
        else:
            sc, _, w = style(name)
            s.path(scurve(xs, ys), f"ln {sc}", w + 0.2, title=name, extra=' opacity=".9"')
        r0, r1 = d.iloc[0]["rank"], d.iloc[-1]["rank"]
        cls = f"lab f-{tok}" if tok else f"tick {style(name)[1]}"
        s.text(x0 - 34, Y(r0) + 3.5, SHORT.get(name, name), cls, "end")
        s.text(x1 + 12, Y(r1) + 3.5, SHORT.get(name, name), cls)
    s.text(x0 - 34, y0 - 16, first, "tick mono m", "end")
    s.text(x1 + 12, y0 - 16, last, "tick mono m")
    s.footer(["Ties broken alphabetically. Hollow marker: batch with fewer than 50 companies."], SOURCE_YC)
    return s.write(FIG / "yc_industry_rank.svg")


# ---------------------------------------------------------------- figure 3: search interest, three stacked panels
def fig_trends(g, embed):
    W, H = 800, 600
    s = Svg(W, H, embed)
    top = s.header("§ Fig 3  ·  Search interest", "b",
                   "Searches for “gpt” barely registered around GPT-3, then took off after ChatGPT",
                   ["Google Trends, worldwide web search, monthly, Sep 2018 to Sep 2026. Each row is indexed to its own peak (100)."])
    x0, x1 = 52, W - 36
    ph, gap, y_top = 112, 30, top + 34
    n = len(g)
    X = lambda i: x0 + i / (n - 1) * (x1 - x0)
    idx = {m: i for i, m in enumerate(g.month)}
    rows = (("ai", "b"), ("gpt", "o"), ("llm", "r"))
    bottom = y_top + 3 * ph + 2 * gap
    for month, label in (("2020-06", "GPT-3 · Jun 2020"), ("2022-11", "ChatGPT · Nov 2022")):
        xe = X(idx[month])
        s.line(xe, y_top - 14, xe, bottom, "ev")
        s.text(xe + 5, y_top - 5, label, "tick mono")
    for k, (term, tok) in enumerate(rows):
        py0 = y_top + k * (ph + gap)
        py1 = py0 + ph
        Y = lambda v: py1 - v / 100 * ph
        for v in (0, 50, 100):
            s.line(x0, Y(v), x1, Y(v), "grid" if v else "axis")
            s.text(x0 - 8, Y(v) + 3.5, str(v), "tick mono m", "end")
        vals = g[term].tolist()
        xs, ys = [X(i) for i in range(n)], [Y(v) for v in vals]
        s.path(polyline(xs, ys) + f" L{xs[-1]:.1f},{Y(0):.1f} L{xs[0]:.1f},{Y(0):.1f} Z", f"area f-{tok}", 0, extra=' stroke="none"')
        s.path(polyline(xs, ys), f"ln s-{tok}", 1.75, title=f'"{term}" search interest')
        s.text(x0 + 8, py0 + 14, f"“{term}”", f"lab mono f-{tok}")
        pk = int(np.argmax(vals))
        pm = pd.Timestamp(g.month[pk] + "-01").strftime("%b %Y")
        s.text(x1, py0 - 5, f"100 = {pm}", "tick mono m", "end")
    # explicit GPT-3 note on the gpt row
    gy0 = y_top + ph + gap
    i20 = idx["2020-07"]
    s.text(X(i20) + 8, gy0 + ph - 22, "below 1 on this index", "tick mono m")
    s.text(X(i20) + 8, gy0 + ph - 10, "through Nov 2022", "tick mono m")
    for i, m in enumerate(g.month):
        if m.endswith("-01"):
            s.text(X(i), bottom + 16, m[:4], "tick mono m", "middle")
            s.line(X(i), bottom, X(i), bottom + 4, "axis")
    s.footer(['Rows are comparable in shape, not level: 100 is each term\'s own busiest month. "gpt" was below 1 every month until Nov 2022.',
              '"llm" before 2022 is mostly the law degree; "gpt" also matched the disk-partition meaning. Google matches terms loosely.'], SOURCE_GT)
    return s.write(FIG / "ai_search_interest.svg")


# ---------------------------------------------------------------- preview + raster
PREVIEW = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Op-ed figures preview</title>
<style>
:root{--background:#fafaf9;--foreground:#131110;--muted-foreground:#6b6865;--border:#dfdedb;--page-rule:#131110;
--roy-r:#f52027;--roy-o:#ee7b00;--roy-y:#ffba06;--roy-b:#0074c9;color-scheme:light}
.dark{--background:#1a1a1a;--foreground:#fafafa;--muted-foreground:#a1a1a1;--border:#ffffff1a;--page-rule:#555;color-scheme:dark}
html,body{margin:0;background:var(--background);color:var(--foreground);font-family:"Open Sans",Arial,sans-serif}
main{max-width:768px;margin:0 auto;padding:0 20px}
figure{margin:32px 0}svg{display:block;width:100%;height:auto}
.solo main{max-width:none;padding:0}.solo figure{margin:0}
button{font:12px ui-monospace,Menlo,monospace;background:none;color:var(--muted-foreground);border:1px dotted var(--border);padding:4px 8px;margin:12px 0}
@page{margin:0}
</style></head><body><main>
<button onclick="document.documentElement.classList.toggle('dark')">toggle light/dark</button>
FIGURES
</main><script>
var q=new URLSearchParams(location.search),t=q.get('theme');
if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark');
if(q.get('fig')){document.documentElement.classList.add('solo');document.querySelector('button').remove();
 document.querySelectorAll('figure').forEach(function(f){if(f.dataset.fig!==q.get('fig'))f.remove()});
 var s=document.querySelector('svg'),vb=s.getAttribute('viewBox').split(' ');
 document.head.insertAdjacentHTML('beforeend','<style>@page{size:'+vb[2]+'px '+vb[3]+'px}</style>')}
</script></body></html>
"""


def write_preview(svgs):
    figs = "".join(f'<figure data-fig="{i + 1}">{p.read_text()}</figure>' for i, p in enumerate(svgs))
    (FIG / "preview.html").write_text(PREVIEW.replace("FIGURES", figs))


def rasterise(svgs):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        print("no Chrome found; skipping PNG/PDF"); return
    url = (FIG / "preview.html").resolve().as_uri()
    base = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--no-pdf-header-footer"]
    for i, p in enumerate(svgs):
        w, h = re.search(r'viewBox="0 0 (\d+) (\d+)"', p.read_text()).groups()
        for theme in ("light", "dark"):
            out = FIG / f"{p.stem}_{theme}.png"
            subprocess.run(base + [f"--screenshot={out}", f"--window-size={w},{h}", "--force-device-scale-factor=2",
                                   f"{url}?fig={i + 1}&theme={theme}"], check=True, capture_output=True)
        subprocess.run(base + [f"--print-to-pdf={FIG / (p.stem + '.pdf')}", f"--window-size={w},{h}",
                               f"{url}?fig={i + 1}&theme=light"], check=True, capture_output=True)
        print("rasterised", p.stem)


def headline_numbers(t, g):
    b2b, ind = (t[t.industry == n].set_index("batch_code") for n in ("B2B", "Industrials"))
    peak = b2b.share_pct.idxmax()
    print(f"B2B: W19 {b2b.share_pct['W19']:.1f}%, peak {peak} {b2b.share_pct[peak]:.1f}%, S26 {b2b.share_pct['S26']:.1f}%, F26 (partial) {b2b.share_pct['F26']:.1f}%")
    print(f"Industrials: W19 {ind.share_pct['W19']:.1f}% rank {ind['rank']['W19']}, S26 {ind.share_pct['S26']:.1f}% rank {ind['rank']['S26']}, F26 (partial) {ind.share_pct['F26']:.1f}% rank {ind['rank']['F26']}")
    for name in HI:
        d = t[(t.industry == name) & ~t.is_partial_batch]
        for seg in ("pre_w23", "w23_on"):
            dd = d[d.segment == seg]; a, _ = fit(dd.pos, dd.share_pct)
            print(f"  {name} {seg} ({dd.batch_code.iloc[0]}–{dd.batch_code.iloc[-1]}): {a:+.2f} pp per batch")
    for term in ("ai", "gpt", "llm"):
        print(f'"{term}": peak {g.month[g[term].idxmax()]}, Nov 2022 {g[term][g.month == "2022-11"].iloc[0]:g}, '
              f'Jul 2020 {g[term][g.month == "2020-07"].iloc[0]:g}')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    ap.add_argument("--embed-fonts", action="store_true")
    a = ap.parse_args()
    for d in (DATA, FIG): d.mkdir(parents=True, exist_ok=True)
    t, g = yc_rows(), trends_rows()
    headline_numbers(t, g)
    svgs = [fig_share(t, a.embed_fonts), fig_rank(t, a.embed_fonts), fig_trends(g, a.embed_fonts)]
    write_preview(svgs)
    print("wrote", ", ".join(p.name for p in svgs), "+ preview.html")
    if not a.no_raster: rasterise(svgs)
