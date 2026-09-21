"""Fig 4: share of each YC batch classified as a full-stack AI company; Fig 5: which YC industries they sit in.

    uv run python fullstack/make_figure.py            # fullstack/figures/yc_fullstack_ai.svg, yc_fullstack_industry.svg + preview.html + PNG (light, dark) + PDF
    uv run python fullstack/make_figure.py --no-raster
    uv run python fullstack/make_figure.py --bare         # figures/bare/: plot-only, styles inlined, transparent PNG (Word / Docs)

Reuses the SVG helpers, tokens and type scale from blog/make_figures.py, so the figure drops into the same page.
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blog"))
import make_figures as mf                                   # noqa: E402

FS = ROOT / "fullstack"
DATA, FIG = FS / "data", FS / "figures"
HI_NAME = "Full-stack AI"
SOURCE = mf.SOURCE_YC
RFS_MONTH, RFS_LABEL = "2025-06", "Full-stack AI RFS · Jun 2025"


def rows():
    b = pd.read_csv(DATA / "yc_fullstack_by_batch.csv")
    b = b[(b.batch_order >= mf.START) & (b.batch_order <= mf.END) & (b.total_companies >= mf.MIN_PLOT_BATCH)].copy()
    b = b[~b.is_partial_batch].sort_values("batch_order").reset_index(drop=True)      # F26 (35 companies) dropped, as in Fig 1 and 2
    b["pos"] = range(len(b))
    return b


def fig(b, embed):
    mf.HI, mf.SHORT = {HI_NAME: "b"}, {}                    # the blog helpers colour whatever is in HI; everything else is gray
    s = mf.Svg(embed)
    first, last = b.iloc[0], b.iloc[-1]
    peak = b.loc[b.full_stack_ai_share_pct.idxmax()]
    top = s.header("§ Fig 4  ·  Full-stack AI companies", "r",
                   f"Full-stack AI companies are {peak.full_stack_ai_share_pct:.0f}% of YC's {peak.batch} batch. "
                   f"Before ChatGPT they were never more than {b[b.batch_order < mf.CUT].full_stack_ai_share_pct.max():.0f}%.",
                   f"Share of each batch's companies that run the service themselves with AI doing the core work "
                   f"(Jared Friedman's definition), {first.batch} to {last.batch}.")
    x0, x1, y0 = 56, mf.W - mf.GUTTER, top + 30
    y1 = y0 + 290
    npos = len(b)
    ymax = max(10, 5 * -(-b.full_stack_ai_share_pct.max() // 5))          # nice ceiling in steps of 5
    X = lambda p: x0 + p / (npos - 1) * (x1 - x0)
    Y = lambda v: y1 - v / ymax * (y1 - y0)
    step = 5 if ymax <= 25 else 10
    for v in range(step, int(ymax) + 1, step):
        s.line(x0, Y(v), x1, Y(v), "grid")
    for v in range(0, int(ymax) + 1, step):
        s.text(x0 - 8, Y(v) + 4, f"{v}%" if v else "0", "tick mono m", "end")
    mf.year_axis(s, y1, x0, x1, [(X(r.pos), r.start_month[:4] if r.start_month.endswith("-01") else None) for _, r in b.iterrows()])
    t = b.rename(columns={"batch_code": "batch_code"})       # month_pos wants batch_code, pos, start_month
    # two event rules: ChatGPT labelled to the right of its rule, the RFS to the left of its own, one line lower
    for code_a, code_b, month, label, dy, anchor in (("S22", "W23", "2022-11", "ChatGPT · Nov 2022", 4, "start"),
                                                     ("S25", "F25", RFS_MONTH, RFS_LABEL, 22, "end")):
        if not ((t.batch_code == code_a).any() and (t.batch_code == code_b).any()): continue
        xe = X(mf.month_pos(t, code_a, code_b, month))
        s.line(xe, y0 - 8, xe, y1, "ev")
        s.text(xe + (6 if anchor == "start" else -6), y0 + dy, label, "tick mono", anchor)
    xs, ys = [X(p) for p in b.pos], [Y(v) for v in b.full_stack_ai_share_pct]
    s.path(mf.polyline(xs, ys), "ln s-b", 3.5, title=HI_NAME)
    for x, y, (_, r) in zip(xs, ys, b.iterrows()):      # invisible hit targets so hovering a batch shows its numbers, as in Fig 1
        s.dot(x, y, 6, "", f"{r.batch}: {r.n_full_stack_ai} of {r.total_companies} companies ({r.full_stack_ai_share_pct:.1f}%)")
        s.add(s.parts.pop().replace('stroke-width="1.8"', 'fill="transparent" stroke="none"'))
    mf.end_labels(s, [HI_NAME], [ys[-1]], [ys[-1]], X(npos - 1))
    s.footer(y1 + 46, ["Each tick is one batch. Classification is ours, not YC's: every company from Winter 2019 on was read against "
                       "a written rubric (fullstack/rubric.md) and the full-stack AI calls were re-read by a second reviewer."], SOURCE)
    FIG.mkdir(exist_ok=True)
    return s.write(FIG / "yc_fullstack_ai.svg")


def industry_rows():
    """Share of each YC top-level industry among full-stack AI companies vs among all companies, same window (full
    batches from Winter 2023 on, i.e. after ChatGPT). A company carries one top-level industry in YC's data."""
    d = pd.read_csv(DATA / "yc_fullstack_labels.csv")
    d = d[(d.batch_order >= mf.CUT) & (d.batch_order <= mf.END) & ~d.is_partial_batch]
    d["industry"] = d.industry.fillna("Unspecified")
    fs = d[d.category == "full_stack_ai"]
    t = pd.DataFrame({"n_full_stack_ai": fs.industry.value_counts(), "n_all": d.industry.value_counts()}).fillna(0).astype(int)
    t["share_full_stack_ai_pct"] = (100 * t.n_full_stack_ai / len(fs)).round(2)
    t["share_all_pct"] = (100 * t.n_all / len(d)).round(2)
    t["ratio"] = (t.share_full_stack_ai_pct / t.share_all_pct).round(2)
    t = t.sort_values("share_full_stack_ai_pct", ascending=False).rename_axis("industry").reset_index()
    t.attrs["window"] = (d.sort_values("batch_order").batch.iloc[0], d.sort_values("batch_order").batch.iloc[-1], len(fs), len(d))
    t.to_csv(DATA / "yc_fullstack_by_industry.csv", index=False)
    return t


def fig_industry(t, embed):
    first, last, n_fs, n_all = t.attrs["window"]
    s = mf.Svg(embed)
    b2b, fin = t.set_index("industry").loc["B2B"], t.set_index("industry").loc["Fintech"]
    top = s.header("§ Fig 5  ·  Where full-stack AI companies sit", "o",
                   f"Full-stack AI companies are less often B2B and {fin.ratio:.1f}× as often Fintech as YC overall",
                   f"Share of YC's top-level industry labels among the {n_fs} full-stack AI companies and among all {n_all:,} "
                   f"companies, {first} to {last}.")
    rows = [r for r in t.itertuples() if r.industry != "Unspecified" and r.n_all >= 20]
    x0, x1, y0 = 200, mf.W - 60, top + 44      # row names end 52px left of the axis so the left value label has room
    short = {"Real Estate and Construction": "Real Estate"}
    rh = 34
    y1 = y0 + rh * (len(rows) - 1)
    xmax = 10 * -(-max(max(r.share_all_pct, r.share_full_stack_ai_pct) for r in rows) // 10)
    X = lambda v: x0 + v / xmax * (x1 - x0)
    for v in range(0, int(xmax) + 1, 10):
        s.line(X(v), y0 - rh // 2, X(v), y1 + rh // 2, "grid")
        s.text(X(v), y1 + rh // 2 + 18, f"{v}%" if v else "0", "tick mono m", "middle")
    for i, r in enumerate(rows):
        y = y0 + i * rh
        xa, xb = X(r.share_all_pct), X(r.share_full_stack_ai_pct)
        s.text(x0 - 52, y + 5, short.get(r.industry, r.industry), "labr", "end")
        s.path(f"M{xa:.1f},{y:.1f} L{xb:.1f},{y:.1f}", "ln bg", 2.2, extra=' opacity="0.3"')
        s.dot(xa, y, 4.2, "bg bgt", f"{r.industry}: {r.share_all_pct:.0f}% of all companies ({r.n_all})")
        s.add(s.parts.pop().replace('stroke-width="1.8"', 'stroke-width="1.8" opacity="0.4"'))
        s.dot(xb, y, 4.2, "s-b f-b", f"{r.industry}: {r.share_full_stack_ai_pct:.0f}% of full-stack AI companies ({r.n_full_stack_ai})")
        # value labels on the outside of each dot
        left, right = (xa, xb) if xa < xb else (xb, xa)
        la, lb = f"{r.share_all_pct:.0f}%", f"{r.share_full_stack_ai_pct:.0f}%"
        if xa < xb:
            s.text(left - 10, y + 4, la, "tick mono m", "end"); s.text(right + 10, y + 4, lb, "tick mono f-b", extra=' font-weight="700"')
        else:
            s.text(left - 10, y + 4, lb, "tick mono f-b", "end", extra=' font-weight="700"'); s.text(right + 10, y + 4, la, "tick mono m")
    # legend on the first row, above the dots
    r0 = rows[0]
    for v, cls, label, anchor in ((r0.share_all_pct, "m", "All companies", "middle"), (r0.share_full_stack_ai_pct, "f-b", "Full-stack AI", "middle")):
        s.text(X(v), y0 - 16, label, f"tick {cls}", anchor, extra=' font-weight="600"')
    s.footer(y1 + rh // 2 + 44, ["Each company carries one top-level industry label from YC. Labels with fewer than 20 companies in the "
                                "window are left out. Fall 2026 (35 companies) is excluded as a partial batch."], SOURCE)
    return s.write(FIG / "yc_fullstack_industry.svg")


def rasterise(svgs):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome: print("no Chrome found; skipping PNG/PDF"); return
    figs = "".join(f'<figure class="article-media article-media-unframed" data-fig="{i + 1}">{p.read_text()}</figure>' for i, p in enumerate(svgs))
    (FIG / "preview.html").write_text(mf.PREVIEW.replace("FIGURES", figs))
    url = (FIG / "preview.html").resolve().as_uri()
    base = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--no-pdf-header-footer"]
    for i, svg in enumerate(svgs):
        w, h = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.read_text()).groups()
        for theme in ("light", "dark"):
            subprocess.run(base + [f"--screenshot={FIG / f'{svg.stem}_{theme}.png'}", f"--window-size={w},{h}",
                                   "--force-device-scale-factor=2", f"{url}?fig={i + 1}&theme={theme}"], check=True, capture_output=True)
        subprocess.run(base + [f"--print-to-pdf={FIG / (svg.stem + '.pdf')}", f"--window-size={w},{h}", f"{url}?fig={i + 1}&theme=light"],
                       check=True, capture_output=True)
        print("rasterised", svg.stem)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    ap.add_argument("--embed-fonts", action="store_true")
    ap.add_argument("--bare", action="store_true", help="plot-only Fig 4 and 5 with inline styles into figures/bare/ (+ transparent PNG)")
    a = ap.parse_args()
    if a.bare:
        mf.BARE, mf.FIG = True, FIG                    # Svg.write then lands in fullstack/figures/bare/ with the blog's flattened styles
        svgs = [fig(rows(), False), fig_industry(industry_rows(), False)]
        mf.rasterise_bare(svgs)
        print("wrote", ", ".join(str(p.relative_to(ROOT)) for p in svgs)); raise SystemExit
    svgs = [fig(rows(), a.embed_fonts), fig_industry(industry_rows(), a.embed_fonts)]
    print("wrote", ", ".join(str(p.relative_to(ROOT)) for p in svgs))
    if not a.no_raster: rasterise(svgs)
