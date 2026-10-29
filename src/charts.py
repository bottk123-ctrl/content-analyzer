"""Построение графиков Plotly. Функции чистые: DataFrame (+тема) -> Figure."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.theme import get_palette

_FONT = "Inter, sans-serif"
_MAX_LABEL = 28


def _rgba(hex_color: str, alpha: float) -> str:
    """#RRGGBB -> rgba(r,g,b,alpha)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _truncate(text: str) -> str:
    """Обрезаем длинные названия, чтобы не ломать разметку графика."""
    text = str(text)
    return text if len(text) <= _MAX_LABEL else text[: _MAX_LABEL - 1] + "…"


def _base_layout(palette: dict, title: str) -> dict:
    """Общие настройки оформления для обоих графиков."""
    return dict(
        title=dict(text=title, font=dict(size=16, color=palette["text"])),
        template=palette["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, color=palette["text"]),
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(font=dict(family=_FONT)),
        showlegend=False,
    )


def views_line_chart(views_df: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Линейный график просмотров по датам с градиентной заливкой."""
    p = get_palette(theme)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=views_df["Дата"],
            y=views_df["Просмотры"],
            mode="lines+markers",
            line=dict(color=p["primary"], width=3, shape="spline"),
            marker=dict(
                size=8, color=p["primary"], line=dict(width=2, color=p["bg"])
            ),
            fill="tozeroy",
            fillgradient=dict(
                type="vertical",
                colorscale=[
                    [0, _rgba(p["primary"], 0.0)],
                    [1, _rgba(p["primary"], 0.35)],
                ],
            ),
            name="Просмотры",
            hovertemplate="%{x|%d.%m.%Y}<br>Просмотры: %{y:,}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(p, "Просмотры по датам"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=p["border"])
    fig.update_yaxes(
        tickformat="~s", gridcolor=p["grid"], zeroline=False, title=None
    )
    return fig


def top_videos_bar_chart(top_df: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Горизонтальная гистограмма Топ-5 видео по лайкам."""
    p = get_palette(theme)
    df = top_df.sort_values("Лайки").copy()  # лидер — сверху
    labels = df["Название"].map(_truncate)
    values_text = [f"{int(v):,}".replace(",", " ") for v in df["Лайки"]]

    fig = go.Figure(
        go.Bar(
            x=df["Лайки"],
            y=labels,
            orientation="h",
            marker=dict(color=p["primary"], line=dict(width=0)),
            text=values_text,
            textposition="outside",
            textfont=dict(color=p["text"], family=_FONT),
            hovertemplate="%{y}<br>Лайки: %{x:,}<extra></extra>",
        )
    )
    layout = _base_layout(p, "Топ-5 видео по лайкам")
    layout["margin"] = dict(l=10, r=40, t=50, b=10)
    fig.update_layout(**layout)
    fig.update_xaxes(
        showgrid=True,
        gridcolor=p["grid"],
        tickformat="~s",
        zeroline=False,
        title=None,
    )
    fig.update_yaxes(showgrid=False, title=None, tickfont=dict(size=12))
    return fig
