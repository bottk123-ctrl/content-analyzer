"""Построение графиков Plotly. Функции чистые: DataFrame -> Figure."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Единая палитра/шаблон для аккуратного вида.
PLOT_TEMPLATE = "plotly_white"
PRIMARY_COLOR = "#4F8BF9"


def views_line_chart(views_df: pd.DataFrame) -> go.Figure:
    """Линейный график просмотров по датам."""
    fig = px.line(
        views_df,
        x="Дата",
        y="Просмотры",
        markers=True,
        template=PLOT_TEMPLATE,
        labels={"Дата": "Дата", "Просмотры": "Просмотры"},
    )
    fig.update_traces(line_color=PRIMARY_COLOR, line_width=3, marker_size=8)
    fig.update_layout(
        title="Просмотры по датам",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def top_videos_bar_chart(top_df: pd.DataFrame) -> go.Figure:
    """Горизонтальная гистограмма Топ-5 видео по лайкам."""
    fig = px.bar(
        top_df.sort_values("Лайки"),  # сортировка, чтобы лидер был сверху
        x="Лайки",
        y="Название",
        orientation="h",
        text="Лайки",
        template=PLOT_TEMPLATE,
        labels={"Лайки": "Лайки", "Название": ""},
    )
    fig.update_traces(marker_color=PRIMARY_COLOR, textposition="outside")
    fig.update_layout(
        title="Топ-5 видео по лайкам",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Лайки",
    )
    return fig
