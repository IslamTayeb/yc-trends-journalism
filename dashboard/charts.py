"""Plotly helpers with the house style used in figures.py, plus era shading."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from eras import Era, PAL

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
FONT = "Inter, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"


def style(fig: go.Figure, height: int = 420, y_title: str | None = None, title: str | None = None,
          legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, title=title, font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor=SURF, plot_bgcolor=SURF, margin=dict(l=10, r=10, t=50 if title else 30, b=10),
        hovermode="x unified", showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=INK2, size=11))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=y_title, tickfont=dict(color=INK2, size=11),
                     rangemode="tozero")
    return fig


def batch_axis(fig: go.Figure, meta: pd.DataFrame, row: int | None = None, col: int | None = None) -> None:
    n = len(meta)
    step = max(1, n // 16)
    ticks = meta.iloc[::step]
    kw = dict(tickvals=ticks["pos"], ticktext=ticks["batch_code"], range=[-0.6, n - 0.4])
    if row is not None:
        fig.update_xaxes(row=row, col=col, **kw)
    else:
        fig.update_xaxes(**kw)


def add_era_bands(fig: go.Figure, eras: list[Era], annotate: bool = True, row=None, col=None) -> None:
    for e in eras:
        kw = dict(x0=e.start_pos - 0.5, x1=e.end_pos + 0.5, fillcolor=e.color, opacity=0.09, line_width=0, layer="below")
        if annotate:
            kw.update(annotation_text=e.name, annotation_position="top left",
                      annotation=dict(font=dict(size=11, color=e.color)))
        if row is not None:
            fig.add_vrect(row=row, col=col, **kw)
        else:
            fig.add_vrect(**kw)
    # era boundaries
    for e in eras[1:]:
        kw = dict(x=e.start_pos - 0.5, line_width=1, line_dash="dot", line_color=INK2, opacity=0.6)
        if row is not None:
            fig.add_vline(row=row, col=col, **kw)
        else:
            fig.add_vline(**kw)


def _symbols(g: pd.DataFrame, hollow_low_tag: bool) -> list[str]:
    flags = g["is_partial_batch"].astype(bool)
    if hollow_low_tag:
        flags = flags | g["low_tag_coverage"].astype(bool)
    return ["circle-open" if f else "circle" for f in flags]


def lines_by_batch(grid: pd.DataFrame, label_col: str, value_col: str, meta: pd.DataFrame, eras: list[Era],
                   hollow_low_tag: bool = False, y_title: str | None = None, height: int = 460,
                   colors: dict[str, str] | None = None) -> go.Figure:
    fig = go.Figure()
    labels = list(grid[label_col].cat.categories) if hasattr(grid[label_col], "cat") else list(grid[label_col].unique())
    for i, lab in enumerate(labels):
        g = grid[grid[label_col] == lab]
        color = (colors or {}).get(lab, PAL[i % len(PAL)])
        fig.add_trace(go.Scatter(
            x=g["pos"], y=g[value_col], mode="lines+markers", name=str(lab),
            line=dict(color=color, width=2), marker=dict(symbol=_symbols(g, hollow_low_tag), size=7, color=color,
                                                          line=dict(width=1.5, color=color)),
            customdata=g[["batch", "count", "total"]].values,
            hovertemplate="%{customdata[0]}<br>" + str(lab) + ": %{y}<br>n=%{customdata[1]} of %{customdata[2]}<extra></extra>",
        ))
    add_era_bands(fig, eras)
    batch_axis(fig, meta)
    return style(fig, height=height, y_title=y_title)


def small_multiples(grid: pd.DataFrame, label_col: str, value_col: str, meta: pd.DataFrame, eras: list[Era],
                    hollow_low_tag: bool = False, ncols: int = 3, y_title: str | None = None) -> go.Figure:
    labels = list(grid[label_col].cat.categories) if hasattr(grid[label_col], "cat") else list(grid[label_col].unique())
    nrows = max(1, -(-len(labels) // ncols))
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=[str(l) for l in labels],
                        shared_xaxes=False, vertical_spacing=0.10, horizontal_spacing=0.06)
    for i, lab in enumerate(labels):
        r, c = i // ncols + 1, i % ncols + 1
        g = grid[grid[label_col] == lab]
        color = PAL[i % len(PAL)]
        fig.add_trace(go.Scatter(
            x=g["pos"], y=g[value_col], mode="lines+markers", name=str(lab), showlegend=False,
            line=dict(color=color, width=2), marker=dict(symbol=_symbols(g, hollow_low_tag), size=6, color=color),
            customdata=g[["batch", "count", "total"]].values,
            hovertemplate="%{customdata[0]}: %{y}<br>n=%{customdata[1]} of %{customdata[2]}<extra></extra>",
        ), row=r, col=c)
        add_era_bands(fig, eras, annotate=False, row=r, col=c)
        batch_axis(fig, meta, row=r, col=c)
    style(fig, height=max(260, 230 * nrows), legend=False)
    fig.update_yaxes(title=None)
    fig.update_annotations(font=dict(size=12))
    return fig


def heatmap(wide: pd.DataFrame, x_title: str = "", value_title: str = "", height: int | None = None,
            colorscale: str = "Blues") -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=wide.values, x=[str(c) for c in wide.columns], y=[str(i) for i in wide.index], colorscale=colorscale,
        colorbar=dict(title=value_title, thickness=12), hoverongaps=False,
        hovertemplate="%{y}<br>%{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(height=height or max(300, 22 * len(wide) + 80), font=dict(family=FONT, color=INK, size=12),
                      paper_bgcolor=SURF, plot_bgcolor=SURF, margin=dict(l=10, r=10, t=20, b=10))
    fig.update_xaxes(title=x_title, side="top", tickfont=dict(size=11))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11))
    return fig


def bump(top: pd.DataFrame, label_col: str, meta: pd.DataFrame, eras: list[Era], n: int) -> go.Figure:
    fig = go.Figure()
    labels = top.groupby(label_col)["rank"].min().sort_values().index
    for i, lab in enumerate(labels):
        g = top[top[label_col] == lab].sort_values("batch_order")
        fig.add_trace(go.Scatter(
            x=g["pos"], y=g["rank"], mode="lines+markers", name=str(lab), connectgaps=False,
            line=dict(color=PAL[i % len(PAL)], width=2), marker=dict(size=7, color=PAL[i % len(PAL)]),
            customdata=g[["batch", "share_pct", "count"]].values,
            hovertemplate="%{customdata[0]}<br>" + str(lab) + " · rank %{y} · %{customdata[1]}% (n=%{customdata[2]})<extra></extra>",
        ))
    add_era_bands(fig, eras)
    batch_axis(fig, meta)
    style(fig, height=max(420, 26 * n + 120), y_title="rank")
    fig.update_yaxes(autorange="reversed", dtick=1, rangemode="normal")
    fig.update_layout(hovermode="closest")
    return fig


def bars(df: pd.DataFrame, x: str, y: str, color: str | None = None, color_map: dict | None = None,
         orientation: str = "v", height: int = 420, y_title: str | None = None, text: bool = False,
         barmode: str = "group") -> go.Figure:
    fig = go.Figure()
    if color:
        for i, (k, g) in enumerate(df.groupby(color, observed=True, sort=False)):
            c = (color_map or {}).get(k, PAL[i % len(PAL)])
            fig.add_trace(go.Bar(x=g[x] if orientation == "v" else g[y], y=g[y] if orientation == "v" else g[x],
                                 name=str(k), marker_color=c, orientation=orientation,
                                 text=g[y].round(1) if text else None, textposition="outside" if text else None))
    else:
        fig.add_trace(go.Bar(x=df[x] if orientation == "v" else df[y], y=df[y] if orientation == "v" else df[x],
                             marker_color=PAL[0], orientation=orientation,
                             text=df[y].round(1) if text else None, textposition="outside" if text else None))
    style(fig, height=height, y_title=y_title if orientation == "v" else None, legend=bool(color))
    fig.update_layout(barmode=barmode, hovermode="closest")
    if orientation == "h":
        fig.update_xaxes(title=y_title, showgrid=True, gridcolor=GRID)
        fig.update_yaxes(autorange="reversed", showgrid=False, rangemode="normal")
    return fig


def diverging_bars(df: pd.DataFrame, label_col: str, value_col: str, height: int | None = None,
                   x_title: str = "") -> go.Figure:
    d = df.sort_values(value_col)
    colors = [PAL[2] if v >= 0 else PAL[7] for v in d[value_col]]
    fig = go.Figure(go.Bar(x=d[value_col], y=d[label_col].astype(str), orientation="h", marker_color=colors,
                           hovertemplate="%{y}: %{x}<extra></extra>"))
    style(fig, height=height or max(300, 22 * len(d) + 80), legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title=x_title, showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=INK2)
    fig.update_yaxes(showgrid=False, rangemode="normal")
    return fig
