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


def _mix(color_a: str, color_b: str, t: float) -> str:
    """Линейная интерполяция двух hex-цветов: t=0 -> a, t=1 -> b."""
    a = color_a.lstrip("#")
    b = color_b.lstrip("#")
    ar, ag, ab = (int(a[i : i + 2], 16) for i in (0, 2, 4))
    br, bg_, bb = (int(b[i : i + 2], 16) for i in (0, 2, 4))
    r = round(ar + (br - ar) * t)
    g = round(ag + (bg_ - ag) * t)
    bl = round(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def _truncate(text: str) -> str:
    """Обрезаем длинные названия, чтобы не ломать разметку графика."""
    text = str(text)
    return text if len(text) <= _MAX_LABEL else text[: _MAX_LABEL - 1] + "…"


def _fmt(value: float) -> str:
    """Число с пробелом как разделителем тысяч."""
    return f"{int(value):,}".replace(",", " ")


def _base_layout(palette: dict) -> dict:
    """Общие настройки оформления для обоих графиков (без заголовка)."""
    return dict(
        template=palette["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, color=palette["text"]),
        margin=dict(l=10, r=10, t=16, b=10),
        hoverlabel=dict(font=dict(family=_FONT)),
        showlegend=False,
    )


def views_line_chart(views_df: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Линейный график просмотров по датам с градиентной заливкой.

    Дополнительно: пунктирная линия среднего и аннотация пикового значения.
    """
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

    if not views_df.empty:
        avg = float(views_df["Просмотры"].mean())
        fig.add_hline(
            y=avg,
            line=dict(color=p["muted"], width=1.4, dash="dot"),
            annotation_text=f"среднее {_fmt(avg)}",
            annotation_position="top left",
            annotation_font=dict(size=11, color=p["muted"]),
        )

        peak = views_df.loc[views_df["Просмотры"].idxmax()]
        fig.add_trace(
            go.Scatter(
                x=[peak["Дата"]],
                y=[peak["Просмотры"]],
                mode="markers",
                marker=dict(
                    size=14, color=p["primary"], line=dict(width=3, color=p["bg"])
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=peak["Дата"],
            y=peak["Просмотры"],
            text=f"макс {_fmt(peak['Просмотры'])}",
            showarrow=True,
            arrowhead=0,
            arrowwidth=1.4,
            arrowcolor=p["primary"],
            ax=0,
            ay=-34,
            font=dict(size=11, color=p["primary"]),
            bgcolor=p["card"],
            bordercolor=p["border"],
            borderwidth=1,
            borderpad=4,
        )

    fig.update_layout(
        **_base_layout(p),
        hovermode="x unified",
        height=400,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=p["border"])
    fig.update_yaxes(
        tickformat="~s", gridcolor=p["grid"], zeroline=False, title=None
    )
    return fig


def top_videos_bar_chart(top_df: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Горизонтальная гистограмма Топ-5 видео по лайкам.

    Цвет баров градиентом по рангу: лидер — насыщенный, ниже — светлее.
    """
    p = get_palette(theme)
    df = top_df.sort_values("Лайки").copy()  # лидер — сверху
    labels = df["Название"].map(_truncate)
    values_text = [_fmt(v) for v in df["Лайки"]]

    n = len(df)
    if n > 1:
        colors = [
            _mix(p["panel"], p["primary"], 0.5 + 0.5 * (i / (n - 1)))
            for i in range(n)
        ]
    else:
        colors = [p["primary"]] * n

    fig = go.Figure(
        go.Bar(
            x=df["Лайки"],
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0), cornerradius=6),
            text=values_text,
            textposition="outside",
            textfont=dict(color=p["text"], family=_FONT, size=12),
            hovertemplate="%{y}<br>Лайки: %{x:,}<extra></extra>",
        )
    )
    layout = _base_layout(p)
    layout["margin"] = dict(l=10, r=52, t=16, b=10)
    layout["height"] = 340
    layout["bargap"] = 0.45
    fig.update_layout(**layout)
    fig.update_xaxes(
        showgrid=True,
        gridcolor=p["grid"],
        tickformat="~s",
        zeroline=False,
        title=None,
        # Запас справа, чтобы подписи значений не обрезались у края.
        range=[0, float(df["Лайки"].max()) * 1.18] if n else None,
    )
    fig.update_yaxes(showgrid=False, title=None, tickfont=dict(size=12))
    return fig
