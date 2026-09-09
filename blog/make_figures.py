"""Op-ed figures, styled to imt.sh, written as self-contained SVG.

    uv run python blog/make_figures.py            # CSVs + SVGs + preview.html + PNG/PDF via headless Chrome
    uv run python blog/make_figures.py --no-raster
    uv run python blog/make_figures.py --embed-fonts   # base64 Open Sans inside the SVGs (bigger, portable)

Colours are CSS custom properties with fallbacks, so the same SVG picks up the site's tokens when inlined on
imt.sh (light and dark) and still renders on its own, following prefers-color-scheme.
"""
import argparse, base64, functools, re, shutil, subprocess
from pathlib import Path
import numpy as np, pandas as pd
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
BLOG, DATA, FIG, FONTS = (ROOT / "blog" / d for d in ("", "data", "figures", "fonts"))
PROC, GT = ROOT / "data/all_years/processed", ROOT / "data/raw/google_trends"
SEASON_MONTH = {"Winter": 1, "Spring": 4, "Summer": 6, "Fall": 9}
START, CUT, END = 20190, 20230, 20263          # W19 .. F26, second trend segment starts at W23
MIN_PLOT_BATCH, MIN_FULL_BATCH = 5, 50         # same thresholds as config.yaml
HI = {"B2B": "b", "Industrials": "o"}          # highlighted series -> roy token
CONTEXT = {"Fintech": ("#e11d48", "#e11d48"), "Healthcare": ("#0f9d8a", "#12a594"), "Consumer": ("#8b5cf6", "#9f7aea")}
BACKGROUND = ["Real Estate and Construction", "Education", "Government"]   # Fig 2 only, one muted gray
# Fig 1 shows five series: the two highlights plus the three labels Industrials overtook (each 400-530 companies in
# the window; the next largest, Real Estate, has 113). Context hues were chosen with the dataviz palette validator
# against the brand blue and orange, all pairs, light and dark: rose instead of the site red, which is too close to the
# orange (delta E 14 normal vision) and crosses Industrials in 2024-26. Dark mode gets its own lighter step per hue.
SHORT = {"Real Estate and Construction": "Real Estate"}   # display name only; YC's label is kept in the data
SOURCE_YC = "Source: YC directory via github.com/yc-oss/api, snapshot 2026-09-06."
SOURCE_GT = "Source: Google Trends, worldwide, monthly, retrieved 2026-09-09."
CREDIT = "Chart: Islam Tayeb · imt.sh"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace'
# canvas: the site's article column is max-w-3xl = 768px, and inline SVG gets all of it, so 1 unit = 1 CSS px there.
# type scale follows the site: figcaption 14px, h3 20px, mono meta 12-14px; nothing below 12px.
W, MARGIN, GUTTER = 768, 24, 132              # GUTTER: right-hand space for direct labels (shared by Fig 1 and 2)
CAP_LH, DEK_LH, H_LH = 19, 19, 26             # line heights for caption, dek, headline
FONT_FILES = {"regular": FONTS / "OpenSans-Regular.ttf", "semibold": FONTS / "OpenSans-SemiBold.ttf",
              "bold": FONTS / "OpenSans-Bold.ttf", "mono": Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")}
CONTEXT_CSS = "".join(f".imt .c{i}{{stroke:{lt}}}.imt .ct{i}{{fill:{lt}}}" for i, (lt, _) in enumerate(CONTEXT.values()))
CONTEXT_DARK = "".join(f".c{i}{{stroke:{dk}}}.ct{i}{{fill:{dk}}}" for i, (_, dk) in enumerate(CONTEXT.values()))


GRAY_ALL = True   # every non-highlighted series in one muted gray (Datawrapper/Economist practice); CONTEXT hues kept for reference
TOP_N = 5         # Fig 1: the N largest labels in the latest full batch; Fig 2: rank rows 1..N plus an "N+1 and below" row


SHADE = {}        # industry -> gray opacity, darkest for the largest context label in the latest full batch (set in main)
GRAY_STEPS = [.5]      # one shade; a size-ordered ramp was tried and rejected (implies a hierarchy that is not the story)


def set_shades(t):
    full = t[(~t.is_partial_batch) & (t.industry != "Unspecified") & ~t.industry.isin(HI)]
    last = full[full.batch_order == full.batch_order.max()].sort_values("share_pct", ascending=False)
    for i, n in enumerate(last.industry):
        SHADE[n] = GRAY_STEPS[min(i, len(GRAY_STEPS) - 1)]


def style(name):
    """(stroke class, fill class, width, opacity) for a non-highlighted series."""
    if name in CONTEXT and not GRAY_ALL:
        i = list(CONTEXT).index(name)
        return f"c{i}", f"ct{i}", 2.0, .7
    return "bg", "bgt", 1.6, SHADE.get(name, .38)


# ---------------------------------------------------------------- data
def yc_rows():
    t = pd.read_csv(PROC / "yc_industry_trends.csv")
    t = t[(t.batch_order >= START) & (t.batch_order <= END) & (t.total_companies >= MIN_PLOT_BATCH)].copy()
    order = sorted(t.batch_order.unique())
    t["pos"] = t.batch_order.map({b: i for i, b in enumerate(order)})
    t["start_month"] = t.batch.map(lambda b: f"{b.split()[1]}-{SEASON_MONTH[b.split()[0]]:02d}")
    t["segment"] = np.where(t.batch_order < CUT, "pre_w23", "w23_on")
    t["year_frac"] = t.start_month.map(lambda m: int(m[:4]) + (int(m[5:]) - 1) / 12)   # for slopes in pts per year
    named = t[t.industry != "Unspecified"].sort_values(["batch_order", "count", "industry"], ascending=[True, False, True])
    named["rank"] = named.groupby("batch_order").cumcount() + 1   # count desc, ties by name (dashboard: method="first")
    t = t.merge(named[["batch_order", "industry", "rank"]], how="left")
    t["rank"] = t["rank"].astype("Int64")
    cols = ["batch_code", "batch", "batch_order", "pos", "start_month", "year_frac", "industry", "count", "total_companies",
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


@functools.lru_cache(maxsize=None)
def _font(face, size):
    f = FONT_FILES[face]
    return ImageFont.truetype(str(f), size * 4) if f.exists() else None   # measure at 4x for sub-pixel accuracy


def text_w(s, size, face="regular", tracking=0.0):
    """Rendered width in px of s at size px. DejaVu Sans Mono is wider than the site's SF Mono / Menlo, so mono is conservative."""
    f = _font(face, size)
    w = f.getlength(s) / 4 if f else 0.55 * size * len(s)
    return w + tracking * size * len(s)


def wrap(text, max_w, size, face="regular", balance=False):
    """Word wrap to max_w px; text may be a list of sentences, which are joined with spaces.
    balance=True keeps the line count but evens the lines out (like the site's text-wrap:balance on headings)."""
    words = (" ".join(text) if isinstance(text, (list, tuple)) else text).split()

    def greedy(limit):
        lines, cur = [], ""
        for w in words:
            cand = f"{cur} {w}".strip()
            if cur and text_w(cand, size, face) > limit: lines.append(cur); cur = w
            else: cur = cand
        return lines + ([cur] if cur else [])

    lines = greedy(max_w)
    if balance and len(lines) == 2:            # two lines: break after a sentence end or comma if both halves fit, else evenly
        cands = []
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            wa, wb = text_w(a, size, face), text_w(b, size, face)
            if max(wa, wb) <= max_w:
                punct = 0 if a.endswith((".", "?", "!")) else 1 if a.endswith((",", ";", ":")) else 2
                cands.append((punct, abs(wa - wb), [a, b]))
        if cands: return min(cands, key=lambda c: c[:2])[2]
    if balance and len(lines) > 1:
        lo, hi = max(text_w(w, size, face) for w in words), max_w
        while hi - lo > 1:                        # smallest width that still gives the same number of lines
            mid = (lo + hi) / 2
            if len(greedy(mid)) == len(lines): hi = mid
            else: lo = mid
        lines = greedy(hi)
    assert all(text_w(l, size, face) <= max_w for l in lines), lines
    return lines


def fit(pos, y):
    a, b = np.polyfit(np.asarray(pos, float), np.asarray(y, float), 1)
    return a, b


# ---------------------------------------------------------------- svg helpers
CSS = """
.imt{--bg:var(--background,#fafaf9);--ink:var(--foreground,#131110);--mut:var(--muted-foreground,#6b6865);
--rule:var(--border,#dfdedb);--prule:var(--page-rule,#131110);--r:var(--roy-r,#f52027);--o:var(--roy-o,#ee7b00);
--y:var(--roy-y,#ffba06);--b:var(--roy-b,#0074c9);font-family:"Open Sans",Arial,sans-serif;font-size:14px}
@media (prefers-color-scheme:dark){.imt{--bg:var(--background,#1a1a1a);--ink:var(--foreground,#fafafa);
--mut:var(--muted-foreground,#a1a1a1);--rule:var(--border,#ffffff1a);--prule:var(--page-rule,#555)}CTXDARK_MEDIA}
.dark .imt{--bg:var(--background,#1a1a1a);--ink:var(--foreground,#fafafa);--mut:var(--muted-foreground,#a1a1a1);
--rule:var(--border,#ffffff1a);--prule:var(--page-rule,#555)}CTXDARK_CLASS
.imt text{fill:var(--ink)}.imt .m{fill:var(--mut)}.imt .mono{font-family:MONO}
.imt .kick{font-size:13px;font-weight:700;letter-spacing:.2em}.imt .h{font-size:20px;font-weight:600}
.imt .dek,.imt .cap{font-size:14px}.imt .tick{font-size:12px}.imt .foot{font-size:12px}.imt .lab{font-size:14px;font-weight:600}.imt .labr{font-size:14px}
.imt .ground{fill:var(--bg)}.imt .grid{stroke:var(--rule);opacity:.7}.imt .axis{stroke:var(--mut);opacity:.6}
.imt .ev{stroke:var(--prule);stroke-width:1.1;stroke-dasharray:1.5 3.5;stroke-linecap:round}
.imt .ln{fill:none;stroke-linejoin:round;stroke-linecap:round}CTXCSS.imt .bg{stroke:var(--mut)}.imt .bgt{fill:var(--mut)}
.imt .trend{stroke-dasharray:5 4;opacity:.8}.imt .hollow{fill:var(--bg)}
.imt .s-r{stroke:var(--r)}.imt .s-o{stroke:var(--o)}.imt .s-y{stroke:var(--y)}.imt .s-b{stroke:var(--b)}
.imt .f-r{fill:var(--r)}.imt .f-o{fill:var(--o)}.imt .f-y{fill:var(--y)}.imt .f-b{fill:var(--b)}
.imt .area{opacity:.12}
""".replace("MONO", MONO).replace("CTXCSS", CONTEXT_CSS) \
    .replace("CTXDARK_MEDIA", CONTEXT_DARK.replace(".c", ".imt .c")) \
    .replace("CTXDARK_CLASS", CONTEXT_DARK.replace(".c", ".dark .imt .c"))


def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    """Parts are collected top-down; the footer fixes the total height, so the opening tag is written last."""
    def __init__(self, embed_fonts=False):
        self.w, self.h, self.parts, self.embed = W, None, [], embed_fonts

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
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="{cls}" stroke-width="1.8">{t}</circle>')

    def header(self, kicker, tok, headline, dek):
        """Kicker, headline (wrapped at 20px semibold), dek (wrapped at 14px). Returns the baseline below the dek."""
        wmax = self.w - 2 * MARGIN
        self.text(MARGIN, 26, kicker.upper(), f"kick mono f-{tok}")
        y = 54
        for line in wrap(headline, wmax, 20, "semibold", balance=True):
            self.text(MARGIN, y, line, "h"); y += H_LH
        y -= H_LH - 22
        for line in wrap(dek, wmax, 14, balance=True):
            self.text(MARGIN, y, line, "dek m"); y += DEK_LH
        return y - DEK_LH

    def footer(self, y, caption, source):
        """Caption paragraph wrapped at 14px from baseline y, then the source/credit line; sets the figure height."""
        lines = wrap(caption, self.w - 2 * MARGIN, 14)
        for line in lines:
            self.text(MARGIN, y, line, "cap m"); y += CAP_LH
        y += 6
        self.text(MARGIN, y, source, "foot mono m")
        self.text(self.w - MARGIN, y, CREDIT, "foot mono m", "end")
        assert text_w(source, 12, "mono") + text_w(CREDIT, 12, "mono") + 24 <= self.w - 2 * MARGIN, "footer line too wide"
        self.h = y + 14
        return lines

    def write(self, path):
        css = CSS + (font_faces() if self.embed else "")
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="100%" class="imt" '
                f'role="img"><style>{css}</style><rect class="ground" width="{self.w}" height="{self.h}"/>')
        path.write_text(head + "".join(self.parts) + "</svg>\n")
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


def steps(xs, ys):
    """Mid-step staircase: flat at each batch's value, vertical jump halfway to the next batch."""
    d = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for (x1, y1), (x2, y2) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        mx = (x1 + x2) / 2
        d.append(f"H{mx:.1f} V{y2:.1f} H{x2:.1f}")
    return " ".join(d)


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


def year_axis(s, y, x0, x1, ticks):
    """One time axis for every figure: baseline at y, 8px major tick with the year centred under it at each year's first
    observation, 4px minor tick at every other observation (batches; monthly data passes only the year ticks)."""
    s.line(x0, y, x1, y, "axis")
    for x, year in ticks:
        s.line(x, y, x, y + (8 if year else 4), "axis")
        if year: s.text(x, y + 22, year, "tick mono m", "middle")


# ---------------------------------------------------------------- figure 1: share lines
def fig_share(t, embed):
    s = Svg(embed)
    top = s.header("§ Fig 1  ·  YC batch composition", "r",
                   "B2B peaked at 69% of a YC batch in 2023. Industrials has tripled since 2019.",
                   "Share of each batch's companies carrying YC's top-level industry label, Winter 2019 to Fall 2026.")
    x0, x1, y0 = 56, W - GUTTER, top + 30
    y1 = y0 + 290                                   # plot area 580 x 290, about 2:1
    batches = t.drop_duplicates("batch_code").sort_values("pos")
    npos = len(batches)
    X = lambda p: x0 + p / (npos - 1) * (x1 - x0)
    Y = lambda v: y1 - v / 75 * (y1 - y0)
    for v in (25, 50, 75):
        s.line(x0, Y(v), x1, Y(v), "grid")
    for v in (0, 25, 50, 75):
        s.text(x0 - 8, Y(v) + 4, f"{v}%" if v else "0", "tick mono m", "end")
    year_axis(s, y1, x0, x1, [(X(b.pos), b.start_month[:4] if b.start_month.endswith("-01") else None) for _, b in batches.iterrows()])
    # ChatGPT rule, same cut as the trend segments
    pcut = month_pos(t, "S22", "W23", "2022-11")
    xe = X(pcut)
    s.line(xe, y0 - 8, xe, y1, "ev")
    s.text(xe + 6, y0 + 4, "ChatGPT · Nov 2022", "tick mono")
    series = lambda name: t[t.industry == name].sort_values("pos")
    last_full = t[(~t.is_partial_batch) & (t.industry != "Unspecified")]
    last_full = last_full[last_full.batch_order == last_full.batch_order.max()].sort_values("share_pct", ascending=False)
    shown = list(last_full.industry.head(TOP_N))
    assert all(h in shown for h in HI), shown
    context = [n for n in shown if n not in HI]
    for name in context:
        d = series(name)
        sc, _, w, al = style(name)
        s.path(polyline([X(p) for p in d.pos], [Y(v) for v in d.share_pct]), f"ln {sc}", w, title=name, extra=f' opacity="{al}"')
    for name, tok in HI.items():
        d = series(name)
        for seg in ("pre_w23", "w23_on"):
            dd = d[d.segment == seg]
            solid = dd[~dd.is_partial_batch]
            a, b = fit(solid.pos, solid.share_pct)
            ay, _ = fit(solid.year_frac, solid.share_pct)   # same fit against calendar time, for a unit readers know
            p0, p1 = (dd.pos.min(), pcut) if seg == "pre_w23" else (pcut, dd.pos.max())   # fits meet at the rule
            s.path(polyline([X(p0), X(p1)], [Y(a * p0 + b), Y(a * p1 + b)]), f"ln trend s-{tok}", 1.6,
                   title=f"{name}, least-squares fit {solid.batch.iloc[0]} to {solid.batch.iloc[-1]}: {ay:+.1f} points per year")
            pm = (p0 + p1) / 2    # slope label on each dashed segment: above for Industrials, below for B2B
            lab = f"{ay:+.1f} pts/yr"
            half = text_w(lab, 12, "mono") / 2 + 6
            near = d[(X(d.pos) >= X(pm) - half) & (X(d.pos) <= X(pm) + half)]   # points the label would sit over
            ys = [Y(a * pm + b)] + [Y(v) for v in near.share_pct]
            y = min(ys) - 18 if name == "Industrials" else max(ys) + 26      # clear of fit, solid line, marker and descenders
            s.text(X(pm), y, lab, f"tick mono f-{tok}", "middle")
        s.path(polyline([X(p) for p in d.pos], [Y(v) for v in d.share_pct]), f"ln s-{tok}", 2.5)
        for _, r in d[d.is_partial_batch].iterrows():   # only the partial batch gets a marker (hollow)
            s.dot(X(r.pos), Y(r.share_pct), 4.2, f"s-{tok} hollow",
                  f"{r.batch_code} · {name} · {r.share_pct:.1f}% ({r['count']} of {r.total_companies})")
    # direct labels at the right edge, nudged apart, with a leader where a label had to move
    names = list(HI) + context
    ends = [Y(series(n).iloc[-1].share_pct) for n in names]
    lys = spread(ends, 22, y0, y1)   # fans the cluster up into the gap below B2B; leaders point back to each line
    end_labels(s, names, ends, lys, X(npos - 1))
    s.footer(y1 + 46, ["Each tick is one batch. Dashed lines show the trend, split at ChatGPT.",
                       "A hollow dot is a batch with under 50 companies, not in the trend."], SOURCE_YC)
    return s.write(FIG / "yc_b2b_vs_industrials.svg")


def end_labels(s, names, ends, lys, xr):
    """Direct labels to the right of the last point (at xr), with a short leader where a label had to move."""
    for name, ye, yl in zip(names, ends, lys):
        tok = HI.get(name)
        op = "" if tok else f' opacity="{max(style(name)[3], .55)}"'
        if abs(yl - ye) > 2:   # leader: short horizontal stub, then a diagonal to the label, same opacity as the label
            s.path(f"M{xr + 5:.1f},{ye:.1f} H{xr + 8:.1f} L{xr + 15:.1f},{yl:.1f}", f"ln {f's-{tok}' if tok else style(name)[0]}", 1, extra=op)
        label = SHORT.get(name, name)
        s.text(xr + 19, yl + 4.5, label, f"lab f-{tok}" if tok else f"labr {style(name)[1]}", extra=op)
        assert xr + 19 + text_w(label, 14, "semibold") <= s.w - 8, label


# ---------------------------------------------------------------- figure 2: rank bump chart
def fig_rank(t, embed, variant="curve", out="yc_industry_rank.svg"):
    """variant: curve (bump chart), step (staircase), slope (first vs last full batch), tiles (rank matrix)."""
    if variant == "tiles": return fig_rank_tiles(t, embed, out)
    if variant == "slope": return fig_rank_slope(t, embed, out)
    connect = steps if variant == "step" else scurve
    s = Svg(embed)
    top = s.header("§ Fig 2  ·  Industry rank per batch", "o",
                   "Industrials went from YC's fifth-largest industry label to its second",
                   "Rank of the eight top-level industry labels by company count within each batch, Winter 2019 to Fall 2026.")
    x0, x1, y0 = 64, W - GUTTER, top + 40
    y1 = y0 + 46 * TOP_N                            # 46 px per rank step, last row is "N+1 and below"
    named = t[t.industry != "Unspecified"]
    batches = named.drop_duplicates("batch_code").sort_values("pos")
    npos = len(batches)
    X = lambda p: x0 + p / (npos - 1) * (x1 - x0)
    Y = lambda r: y0 + (min(int(r), TOP_N + 1) - 1) / TOP_N * (y1 - y0)
    for r in range(1, TOP_N + 1):
        s.line(x0, Y(r), x1, Y(r), "grid")
        s.text(x0 - 12, Y(r) + 4, f"#{r}", "tick mono m", "end")
    s.text(x0 - 12, Y(TOP_N + 1) + 4, f"#{TOP_N + 1}+", "tick mono m", "end")
    year_axis(s, y1, x0, x1, [(X(b.pos), b.start_month[:4] if b.start_month.endswith("-01") else None) for _, b in batches.iterrows()])
    xe = X(month_pos(t, "S22", "W23", "2022-11"))
    s.line(xe, y0 - 26, xe, y1, "ev")
    s.text(xe + 6, y0 - 16, "ChatGPT · Nov 2022", "tick mono")
    reach = named[~named.is_partial_batch].groupby("industry")["rank"].min()   # full batches only
    shown = [n for n in BACKGROUND + list(CONTEXT) if reach[n] <= TOP_N] + list(HI)   # every label that ever makes the top N
    ends = []
    for name in shown:
        d = named[named.industry == name].sort_values("pos")
        tok = HI.get(name)
        xs, ys = [X(p) for p in d.pos], [Y(r) for r in d["rank"]]
        if tok:
            s.path(connect(xs, ys), f"ln s-{tok}", 3.2)
            for _, r in d[d.is_partial_batch].iterrows():   # only the partial batch gets a marker (hollow)
                s.dot(X(r.pos), Y(r["rank"]), 4.8, f"s-{tok} hollow",
                      f"{r.batch_code} · {name} · rank {r['rank']} ({r['count']} companies)")
        else:
            sc, _, w, al = style(name)
            s.path(connect(xs, ys), f"ln {sc}", w + 0.2, title=name, extra=f' opacity="{al}"')
        r1 = d.iloc[-1]["rank"]
        ends.append((name, Y(r1)))
    names = [n for n, _ in ends]
    lys = spread([y for _, y in ends], 20, y0, y1 + 8)
    end_labels(s, names, [y for _, y in ends], lys, x1)
    s.footer(y1 + 48, [f"Each tick is one batch. Ranks below #{TOP_N} are shown as #{TOP_N + 1}+.",
                       "A hollow dot is a batch with under 50 companies."], SOURCE_YC)
    return s.write(FIG / out)


def _rank_shown(t):
    named = t[t.industry != "Unspecified"]
    reach = named[~named.is_partial_batch].groupby("industry")["rank"].min()
    return named, [n for n in BACKGROUND + list(CONTEXT) if reach[n] <= TOP_N] + list(HI)


def fig_rank_slope(t, embed, out):
    """Two columns: rank in the first batch and in the last full batch, one straight line per label."""
    s = Svg(embed)
    top = s.header("§ Fig 2  ·  Industry rank, first vs latest batch", "o",
                   "Industrials went from YC's fifth-largest industry label to its second",
                   "Rank of the eight top-level industry labels by company count, Winter 2019 and Summer 2026.")
    named, shown = _rank_shown(t)
    full = named[~named.is_partial_batch]
    first, last = full[full.batch_order == full.batch_order.min()], full[full.batch_order == full.batch_order.max()]
    x0, x1, y0 = 64 + 90, W - GUTTER - 90, top + 40
    y1 = y0 + 46 * TOP_N
    Y = lambda r: y0 + (min(int(r), TOP_N + 1) - 1) / TOP_N * (y1 - y0)
    for r in range(1, TOP_N + 1):
        s.line(x0, Y(r), x1, Y(r), "grid")
    s.line(x0, Y(TOP_N + 1), x1, Y(TOP_N + 1), "axis")
    for x, b in ((x0, first.batch.iloc[0]), (x1, last.batch.iloc[0])):
        s.text(x, y1 + 22, b, "tick mono m", "middle")
    for name in shown:
        tok = HI.get(name)
        ra, rb = first[first.industry == name]["rank"].iloc[0], last[last.industry == name]["rank"].iloc[0]
        sc, _, w, al = style(name)
        cls, sw, op = (f"ln s-{tok}", 3.2, "") if tok else (f"ln {sc}", w + 0.2, f' opacity="{al}"')
        s.path(polyline([x0, x1], [Y(ra), Y(rb)]), cls, sw, title=name, extra=op)
        for x, r in ((x0, ra), (x1, rb)):
            s.dot(x, Y(r), 4.2, f"s-{tok} f-{tok}" if tok else f"{sc} {style(name)[1]}", f"{name} rank {r}")
        lab_cls = f"lab f-{tok}" if tok else f"labr {style(name)[1]}"
        s.text(x0 - 14, Y(ra) + 4.5, f"#{ra}  {SHORT.get(name, name)}", lab_cls, "end", extra=op)
        s.text(x1 + 14, Y(rb) + 4.5, f"{SHORT.get(name, name)}  #{rb}", lab_cls, extra=op)
    s.footer(y1 + 46, [f"Ranks below #{TOP_N} are shown as #{TOP_N + 1}+. Summer 2026 is the latest batch with 50 or more companies."], SOURCE_YC)
    return s.write(FIG / out)


def fig_rank_tiles(t, embed, out):
    """Rank matrix: one row per label, one column per batch, the rank number in a cell shaded by rank."""
    s = Svg(embed)
    top = s.header("§ Fig 2  ·  Industry rank per batch", "o",
                   "Industrials went from YC's fifth-largest industry label to its second",
                   "Rank of the eight top-level industry labels by company count within each batch, Winter 2019 to Fall 2026.")
    named, shown = _rank_shown(t)
    batches = named.drop_duplicates("batch_code").sort_values("pos")
    npos = len(batches)
    last = named[(~named.is_partial_batch)]; last = last[last.batch_order == last.batch_order.max()].set_index("industry")["rank"]
    rows = sorted(shown, key=lambda n: last[n])
    x0, x1, y0 = 64, W - GUTTER, top + 40
    cw, ch = (x1 - x0) / npos, 30
    y1 = y0 + ch * len(rows)
    for i, name in enumerate(rows):
        tok = HI.get(name)
        d = named[named.industry == name].set_index("pos")["rank"]
        cy = y0 + i * ch
        for _, b in batches.iterrows():
            r = int(d[b.pos]); rr = min(r, TOP_N + 1)
            cx = x0 + b.pos * cw
            fill = f"f-{tok}" if tok else "bgt"
            op = .12 + .78 * (TOP_N + 1 - rr) / TOP_N         # rank 1 darkest, N+1 lightest
            s.add(f'<rect x="{cx + 1:.1f}" y="{cy + 1:.1f}" width="{cw - 2:.1f}" height="{ch - 2:.1f}" class="{fill}" opacity="{op:.2f}">'
                  f"<title>{esc(b.batch_code)} · {esc(name)} · rank {r}</title></rect>")
            s.text(cx + cw / 2, cy + ch / 2 + 4, str(r) if r <= TOP_N else f"{TOP_N + 1}+", "tick mono", "middle",
                   extra=' style="fill:var(--ink)"' if op < .5 else ' style="fill:var(--bg)"')
        s.text(x1 + 19, cy + ch / 2 + 4.5, SHORT.get(name, name), f"lab f-{tok}" if tok else "labr m")
    year_axis(s, y1, x0, x1, [(x0 + (b.pos + .5) * cw, b.start_month[:4] if b.start_month.endswith("-01") else None) for _, b in batches.iterrows()])
    xe = x0 + (month_pos(t, "S22", "W23", "2022-11") + .5) * cw
    s.line(xe, y0 - 26, xe, y1, "ev")
    s.text(xe + 6, y0 - 16, "ChatGPT · Nov 2022", "tick mono")
    s.footer(y1 + 48, [f"Each column is one batch. Darker means a higher rank; ranks below #{TOP_N} are shown as {TOP_N + 1}+.",
                       "Fall 2026 has under 50 companies."], SOURCE_YC)
    return s.write(FIG / out)


# ---------------------------------------------------------------- figure 3: search interest, three stacked panels
def fig_trends(g, embed):
    s = Svg(embed)
    top = s.header("§ Fig 3  ·  Search interest", "b",
                   "Searches for “gpt” barely registered around GPT-3, then took off after ChatGPT",
                   "Google Trends, worldwide web search, monthly, Sep 2018 to Sep 2026. Each row is indexed to its own peak.")
    x0, x1 = 56, W - 32                          # term labels sit inside the panels, so the plot runs to the right margin
    ph, gap, y_top = 112, 32, top + 36
    n = len(g)
    X = lambda i: x0 + i / (n - 1) * (x1 - x0)
    idx = {m: i for i, m in enumerate(g.month)}
    rows = (("ai", "b"), ("gpt", "o"), ("llm", "r"))
    bottom = y_top + 3 * ph + 2 * gap
    for month, label in (("2020-06", "GPT-3 · Jun 2020"), ("2022-11", "ChatGPT · Nov 2022")):
        xe = X(idx[month])
        s.line(xe, y_top - 16, xe, bottom, "ev")
        s.text(xe + 6, y_top - 6, label, "tick mono")
    for k, (term, tok) in enumerate(rows):
        py0 = y_top + k * (ph + gap)
        py1 = py0 + ph
        Y = lambda v: py1 - v / 100 * ph
        for v in (0, 50, 100):
            if v: s.line(x0, Y(v), x1, Y(v), "grid")
            elif k < 2: s.line(x0, Y(v), x1, Y(v), "axis")   # the last panel's baseline comes from year_axis
            s.text(x0 - 8, Y(v) + 4, str(v), "tick mono m", "end")
        vals = g[term].tolist()
        xs, ys = [X(i) for i in range(n)], [Y(v) for v in vals]
        s.path(polyline(xs, ys) + f" L{xs[-1]:.1f},{Y(0):.1f} L{xs[0]:.1f},{Y(0):.1f} Z", f"area f-{tok}", 0, extra=' stroke="none"')
        s.path(polyline(xs, ys), f"ln s-{tok}", 2, title=f'"{term}" search interest')
        s.text(x0 + 8, py0 + 16, f"“{term}”", f"lab mono f-{tok}")
    year_axis(s, bottom, x0, x1, [(X(i), m[:4]) for i, m in enumerate(g.month) if m.endswith("-01")])
    s.footer(bottom + 44, ["Each row is scaled to its own busiest month, which is 100. So the rows show shape, not size.",
                           "Before 2022, most searches for “llm” were about the law degree."], SOURCE_GT)
    return s.write(FIG / "ai_search_interest.svg")


# ---------------------------------------------------------------- preview + raster
PREVIEW = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Op-ed figures preview</title>
<style>
:root{--background:#fafaf9;--foreground:#131110;--muted-foreground:#6b6865;--border:#dfdedb;--page-rule:#131110;
--roy-r:#f52027;--roy-o:#ee7b00;--roy-y:#ffba06;--roy-b:#0074c9;color-scheme:light}
.dark{--background:#1a1a1a;--foreground:#fafafa;--muted-foreground:#a1a1a1;--border:#ffffff1a;--page-rule:#555;color-scheme:dark}
html,body{margin:0;background:var(--background);color:var(--foreground);font-family:"Open Sans",Arial,sans-serif}
main{max-width:768px;margin:0 auto;padding:0 20px;font-size:16px;line-height:1.625}   /* the site's article column and body copy */
p{margin:16px 0}p.m{color:var(--muted-foreground);font-size:14px;line-height:1.375;font-style:italic;text-align:center}
figure{margin:20px 0;max-width:100%}svg{display:block;width:100%;height:auto}   /* article-media-unframed: no 10px frame */
.solo main{max-width:none;padding:0}.solo figure{margin:0}.solo p{display:none}
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


LOREM = ("Body copy at the site's 16px / 1.625 so the figure can be judged against the type it will sit between. YC's "
         "batches are the unit here: every company that goes through the accelerator is stamped with a season and a year, "
         "and the directory keeps that label long after the company has changed what it does.")


VARIANTS = (("curve", "Bump chart, curved connectors (current)"), ("step", "Staircase: flat per batch, vertical jumps"),
            ("slope", "Slope chart: first batch vs latest full batch"), ("tiles", "Rank matrix: one cell per batch"))


def write_variants(t, embed):
    parts = []
    for v, title in VARIANTS:
        p = fig_rank(t, embed, v, f"fig2_{v}.svg")
        parts.append(f'<h2>{title}</h2><figure class="article-media article-media-unframed">{p.read_text()}</figure>')
    html = PREVIEW.replace("FIGURES", "".join(parts)).replace("<title>Op-ed figures preview</title>", "<title>Fig 2 variants</title>")
    html = html.replace("</style>", "h2{font:600 16px 'Open Sans',Arial,sans-serif;margin:40px 0 4px;color:var(--muted-foreground)}</style>")
    (FIG / "fig2_variants.html").write_text(html)


def write_preview(svgs):
    figs = "".join(f'<figure class="article-media article-media-unframed" data-fig="{i + 1}">{p.read_text()}</figure>'
                   + (f"<p>{LOREM}</p>" if i == 0 else "") for i, p in enumerate(svgs))
    (FIG / "preview.html").write_text(PREVIEW.replace("FIGURES", f"<p>{LOREM}</p>" + figs))


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
            dd = d[d.segment == seg]; a, _ = fit(dd.pos, dd.share_pct); ay, _ = fit(dd.year_frac, dd.share_pct)
            print(f"  {name} {seg} ({dd.batch_code.iloc[0]}–{dd.batch_code.iloc[-1]}): {a:+.2f} pp per batch, {ay:+.2f} pp per year")
    for term in ("ai", "gpt", "llm"):
        print(f'"{term}": peak {g.month[g[term].idxmax()]}, Nov 2022 {g[term][g.month == "2022-11"].iloc[0]:g}, '
              f'Jul 2020 {g[term][g.month == "2020-07"].iloc[0]:g}')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    ap.add_argument("--embed-fonts", action="store_true")
    ap.add_argument("--variants", action="store_true", help="also write fig2_{curve,step,slope,tiles}.svg and fig2_variants.html")
    a = ap.parse_args()
    for d in (DATA, FIG): d.mkdir(parents=True, exist_ok=True)
    t, g = yc_rows(), trends_rows()
    set_shades(t)
    headline_numbers(t, g)
    svgs = [fig_share(t, a.embed_fonts), fig_rank(t, a.embed_fonts), fig_trends(g, a.embed_fonts)]
    write_preview(svgs)
    if a.variants: write_variants(t, a.embed_fonts)
    print("wrote", ", ".join(p.name for p in svgs), "+ preview.html")
    if not a.no_raster: rasterise(svgs)
