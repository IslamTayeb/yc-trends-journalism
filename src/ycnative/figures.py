"""Charts. Share-of-batch on y, batches in chronological order on x. Partial / low-tag-coverage batches are drawn hollow."""
from __future__ import annotations
import re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd

PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "text.color": INK,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titleweight": "semibold", "axes.titlesize": 12,
                     "legend.frameon": False, "figure.dpi": 150})

def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

class Figs:
    def __init__(self, ctx):
        self.c = ctx; self.cfg = ctx["cfg"]; self.dir = self.cfg["FIG"]
        self.bm = ctx["bmeta"].set_index("batch")
        self.batches = [b for b in ctx["batches"] if self.bm.loc[b, "total_companies"] >= self.cfg.get("MIN_PLOT_BATCH", 5)]
        self.codes = [self.bm.loc[b, "batch_code"] for b in self.batches]
        self.partial = {b for b in self.batches if self.bm.loc[b, "is_partial_batch"]}
        self.lowtag = set(ctx["low_tag_batches"]); self.made = []

    def _x(self, ax, note=True):
        ax.set_xticks(range(len(self.batches))); ax.set_xticklabels(self.codes, rotation=45, ha="right")
        if note and self.partial:
            ax.annotate("hollow markers = in-progress batch (< %d companies)" % self.cfg["MIN_FULL_BATCH"], xy=(0, -0.28), xycoords="axes fraction", fontsize=8, color=INK2)

    def _line(self, ax, series, label, color, tagbased=False):
        x = np.arange(len(self.batches)); y = np.array([series.get(b, np.nan) for b in self.batches], float)
        ax.plot(x, y, color=color, lw=2, label=label)
        for i, b in enumerate(self.batches):
            hollow = b in self.partial or (tagbased and b in self.lowtag)
            ax.plot(x[i], y[i], marker="o", ms=6, mfc=SURF if hollow else color, mec=color, mew=1.5)

    def save(self, fig, name):
        p = self.dir / f"{name}.png"; fig.tight_layout(); fig.savefig(p, bbox_inches="tight"); plt.close(fig); self.made.append(p.name); return p

    def batch_size(self):
        bs = self.c["bs"]; bs = bs[bs["batch"].isin(self.batches)]; fig, ax = plt.subplots(figsize=(9, 4))
        cols = [SURF if p else PAL[0] for p in bs["is_partial_batch"]]
        ax.bar(range(len(bs)), bs["total_companies"], color=cols, edgecolor=PAL[0], linewidth=1.2, width=0.7)
        for i, v in enumerate(bs["total_companies"]): ax.text(i, v + 4, str(v), ha="center", fontsize=8, color=INK2)
        ax.set_title("YC batch size (publicly listed companies per batch)"); ax.set_ylabel("companies"); self._x(ax)
        return self.save(fig, "batch_size_over_time")

    def multi(self, shares, labels, title, name, ylabel="% of batch", tagbased=False):
        labels = [l for l in labels if l in shares.index][:8]
        if not labels: return None
        fig, ax = plt.subplots(figsize=(9.5, 4.8))
        for i, l in enumerate(labels): self._line(ax, shares.loc[l], l, PAL[i], tagbased)
        ax.set_title(title); ax.set_ylabel(ylabel); ax.set_ylim(bottom=0); self._x(ax)
        ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9)
        if tagbased and self.lowtag:
            ax.annotate("hollow = batch with unreliable tag coverage (%s)" % ", ".join(self.bm.loc[b, "batch_code"] for b in self.lowtag), xy=(0, -0.34), xycoords="axes fraction", fontsize=8, color=INK2)
        return self.save(fig, name)

    def single(self, shares, counts, label, kind, name=None):
        if label not in shares.index: return None
        fig, ax = plt.subplots(figsize=(8, 3.8))
        self._line(ax, shares.loc[label], label, PAL[0], tagbased=(kind == "tag"))
        for i, b in enumerate(self.batches):
            ax.text(i, shares.loc[label, b] + 0.15, str(int(counts.loc[label, b])), ha="center", fontsize=7, color=INK2)
        ax.set_title(f"{kind}: {label}  (share of batch; numbers = company count)"); ax.set_ylabel("% of batch"); ax.set_ylim(bottom=0); self._x(ax)
        return self.save(fig, name or f"{kind}_{slug(label)}")

    def derived_union(self, kind, labels, family):
        """Explicitly derived aggregate: companies carrying ANY of the listed YC labels (union, not sum)."""
        df = self.c["df"]; col = {"tag": "n_tags_norm", "subindustry": "n_subindustry_child"}[kind]
        present = [l for l in labels if l in set(x for v in df[col] for x in (v if isinstance(v, list) else [v]))]
        if not present: return None
        if kind == "tag": hit = df[col].map(lambda v: bool(set(v) & set(present)))
        else: hit = df[col].isin(present)
        s = (100 * hit.groupby(df["batch"]).mean()).reindex(self.batches)
        fig, ax = plt.subplots(figsize=(8, 3.8)); self._line(ax, s, family, PAL[1], tagbased=(kind == "tag"))
        ax.set_title(f"DERIVED aggregation: share of batch with any {kind} in {{{', '.join(present)}}}"); ax.set_ylabel("% of batch"); ax.set_ylim(bottom=0); self._x(ax)
        return self.save(fig, f"derived_union_{kind}_{slug(family)}")

    def movers(self, stats, label_col, kind, n=8):
        st = stats[stats["total_companies"] >= self.cfg["NEW_LABEL_MIN_COUNT"]]
        up = st.sort_values("pp_change", ascending=False).head(n); dn = st.sort_values("pp_change").head(n)
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        for ax, d, t, colr in ((axes[0], up, "largest gains", PAL[2]), (axes[1], dn, "largest declines", PAL[7])):
            ax.barh(d[label_col][::-1], d["pp_change"][::-1], color=colr, height=0.6)
            ax.set_title(f"{kind}: {t} (pp of batch, {self.cfg['START_YEAR']} -> {d['latest_full_batch'].iloc[0]})"); ax.set_xlabel("percentage-point change"); ax.grid(axis="y", visible=False)
        return self.save(fig, f"fastest_moving_{kind}")

    def concentration(self):
        d = self.c["div"].set_index("batch").reindex(self.batches)
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
        self._line(axes[0], d["top5_industry_share_pct"], "top-5 industry share", PAL[0]); axes[0].set_title("Top-5 industry share of batch (%)")
        self._line(axes[1], d["industry_hhi"], "industry HHI", PAL[1]); axes[1].set_title("Industry concentration (HHI, 0-1)")
        self._line(axes[2], d["industry_entropy_normalised"], "normalised industry entropy", PAL[2]); axes[2].set_title("Industry diversity (normalised entropy)")
        for ax in axes: self._x(ax, note=False); ax.set_ylim(bottom=0)
        return self.save(fig, "industry_concentration_over_time")

    def tag_diversity(self):
        d = self.c["div"].set_index("batch").reindex(self.batches)
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
        self._line(axes[0], d["unique_tags"], "unique tags", PAL[0], True); axes[0].set_title("Unique tags used in batch")
        self._line(axes[1], d["rarefied_unique_tags"], "rarefied", PAL[1], True); axes[1].set_title(f"Unique tags per {self.cfg['RAREFY_N']} companies (rarefied)")
        self._line(axes[2], d["tag_entropy_normalised"], "tag entropy", PAL[2], True); axes[2].set_title("Tag diversity (normalised entropy)")
        for ax in axes: self._x(ax, note=False); ax.set_ylim(bottom=0)
        return self.save(fig, "tag_diversity_over_time")

    def geography(self):
        g = self.c["geo"].set_index("batch").reindex(self.batches)
        fig, ax = plt.subplots(figsize=(9, 4))
        self._line(ax, g["us_share_pct"], "US (regions contains 'United States of America')", PAL[0])
        self._line(ax, g["non_us_share_pct"], "non-US", PAL[1]); self._line(ax, g["remote_any_share_pct"], "any remote flag", PAL[2])
        ax.set_title("Headquarters/location fields by batch (% of batch)"); ax.set_ylim(0, 100); self._x(ax); ax.legend(fontsize=8)
        return self.save(fig, "geography_us_vs_non_us")

    def rfs(self):
        ed = self.c["ed"]; ed = ed[ed["era"] != "essays"].sort_values("edition_order")
        fig, ax = plt.subplots(figsize=(10, 4)); cols = [PAL[0] if e == "consolidated" else PAL[1] for e in ed["era"]]
        ax.bar(range(len(ed)), ed["n_requests"], color=cols, width=0.7)
        ax.set_xticks(range(len(ed))); ax.set_xticklabels(ed["edition_label"].str.replace("undated version first captured ", "undated ", regex=False), rotation=45, ha="right", fontsize=8)
        ax.set_title("Requests for Startups: number of requests per edition (blue = consolidated page, orange = seasonal edition)"); ax.set_ylabel("requests"); ax.grid(axis="x", visible=False)
        return self.save(fig, "rfs_requests_per_edition")

    def rfs_mentions(self, top=12):
        m = self.c["per_ed"]; m = m[(m["era"] != "essays") & (m["label_type"] == "tag")]
        if m.empty: return None
        tot = m.groupby("label")["requests_mentioning"].sum().sort_values(ascending=False).head(top).index
        eds = m.drop_duplicates("edition_label").sort_values("edition_order")["edition_label"].tolist()
        M = m[m["label"].isin(tot)].pivot_table(index="label", columns="edition_label", values="requests_mentioning", fill_value=0).reindex(index=tot, columns=eds).fillna(0)
        fig, ax = plt.subplots(figsize=(11, 4.5)); im = ax.imshow(M.values, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(eds))); ax.set_xticklabels([e.replace("undated version first captured ", "undated ") for e in eds], rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(tot))); ax.set_yticklabels(tot, fontsize=9); ax.grid(False)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = int(M.iat[i, j]);
                if v: ax.text(j, i, v, ha="center", va="center", fontsize=7, color="white" if v >= M.values.max() * 0.6 else INK)
        ax.set_title("YC tag names appearing verbatim in RFS request text (requests mentioning; exact string match)")
        fig.colorbar(im, ax=ax, shrink=0.7, label="requests"); return self.save(fig, "rfs_tag_name_mentions_by_edition")

def make_all(ctx):
    F = Figs(ctx); R = ctx["results"]; cfg = ctx["cfg"]
    F.batch_size()
    ind = R["industry"]; F.multi(ind["shares"], list(ind["stats"]["industry"]), "Industries as share of batch (YC top-level `industry` field)", "largest_industries_share")
    F.movers(ind["stats"], "industry", "industry", n=8)
    sub = R["subindustry"]; F.movers(sub["stats"], "subindustry", "subindustry", n=10)
    F.multi(sub["shares"], list(sub["stats"].sort_values("pp_change", ascending=False)["subindustry"].head(8)), "Fastest-growing subindustries (share of batch)", "fastest_growing_subindustries")
    tag = R["tag"]; F.movers(tag["stats"], "tag", "tag", n=10)
    F.multi(tag["shares"], list(tag["stats"].sort_values("pp_change", ascending=False)["tag"].head(8)), "Fastest-growing tags (share of batch)", "fastest_growing_tags", tagbased=True)
    F.multi(tag["shares"], list(tag["stats"]["tag"].head(8)), "Largest tags in latest full batch (share of batch)", "largest_tags_share", tagbased=True)
    # standalone native categories (exact YC labels only)
    for lab in cfg["STANDALONE_INDUSTRIES"]: F.single(ind["shares"], ind["counts"], lab, "industry")
    child_to_full = {}
    for full in sub["shares"].index:
        if "->" in full: child_to_full[full.split("->")[1].strip()] = full
    for lab in cfg["STANDALONE_SUBINDUSTRIES"]:
        if lab in child_to_full: F.single(sub["shares"], sub["counts"], child_to_full[lab], "subindustry", name=f"subindustry_{slug(lab)}")
    for lab in cfg["STANDALONE_TAGS"]: F.single(tag["shares"], tag["counts"], lab, "tag")
    F.derived_union("tag", ["Robotics", "Hard Tech", "Hardware", "Manufacturing", "Drones", "Aerospace", "Semiconductors", "Defense"], "hard-tech-like tag family")
    F.derived_union("subindustry", ["Manufacturing and Robotics", "Defense", "Aviation and Space", "Drones", "Energy", "Industrial Bio", "Automotive", "Climate"], "Industrials children")
    F.concentration(); F.tag_diversity(); F.geography(); F.rfs(); F.rfs_mentions()
    return F.made
