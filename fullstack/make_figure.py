"""Fig 4: share of each YC batch classified as a full-stack AI company, styled like the blog figures.

    uv run python fullstack/make_figure.py            # fullstack/figures/yc_fullstack_ai.svg + preview.html + PNG (light, dark) + PDF
    uv run python fullstack/make_figure.py --no-raster

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
    top = s.header("§ Fig 4  ·  Full-stack AI companies", "b",
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
    for x, y, (_, r) in zip(xs, ys, b.iterrows()):
        s.dot(x, y, 3.2, "s-b f-b", f"{r.batch}: {r.n_full_stack_ai} of {r.total_companies} companies ({r.full_stack_ai_share_pct:.1f}%)")
    mf.end_labels(s, [HI_NAME], [ys[-1]], [ys[-1]], X(npos - 1))
    s.footer(y1 + 46, ["Each dot is one batch. Classification is ours, not YC's: every company from Winter 2019 on was read against "
                       "a written rubric (fullstack/rubric.md) and the full-stack AI calls were re-read by a second reviewer."], SOURCE)
    FIG.mkdir(exist_ok=True)
    return s.write(FIG / "yc_fullstack_ai.svg")


def rasterise(svg):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome: print("no Chrome found; skipping PNG/PDF"); return
    html = mf.PREVIEW.replace("FIGURES", f'<figure class="article-media article-media-unframed" data-fig="1">{svg.read_text()}</figure>')
    (FIG / "preview.html").write_text(html)
    url = (FIG / "preview.html").resolve().as_uri()
    w, h = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.read_text()).groups()
    base = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--no-pdf-header-footer"]
    for theme in ("light", "dark"):
        subprocess.run(base + [f"--screenshot={FIG / f'{svg.stem}_{theme}.png'}", f"--window-size={w},{h}",
                               "--force-device-scale-factor=2", f"{url}?fig=1&theme={theme}"], check=True, capture_output=True)
    subprocess.run(base + [f"--print-to-pdf={FIG / (svg.stem + '.pdf')}", f"--window-size={w},{h}", f"{url}?fig=1&theme=light"],
                   check=True, capture_output=True)
    print("rasterised", svg.stem)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-raster", action="store_true")
    ap.add_argument("--embed-fonts", action="store_true")
    a = ap.parse_args()
    b = rows()
    p = fig(b, a.embed_fonts)
    print("wrote", p.relative_to(ROOT))
    if not a.no_raster: rasterise(p)
