"""Расчёт ключевых метрик (KPI) и агрегаций по данным."""

from __future__ import annotations

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Считаем сводные показатели.

    Возвращает словарь:
        n_videos    - общее количество видео
        total_views - суммарные просмотры
        avg_er      - средний ER, %
    """
    total_views = int(df["Просмотры"].sum())
    n_videos = int(len(df))

    # ER = (Лайки + Комментарии) / Просмотры * 100.
    # Просмотры == 0 заменяем на NaN, чтобы не делить на ноль.
    views = df["Просмотры"].astype(float).where(df["Просмотры"] != 0)
    engagements = (df["Лайки"] + df["Комментарии"]).astype(float)
    er_series = (engagements / views * 100).dropna()
    avg_er = float(er_series.mean()) if not er_series.empty else 0.0

    return {
        "n_videos": n_videos,
        "total_views": total_views,
        "avg_er": avg_er,
    }


def views_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Суммарные просмотры, сгруппированные по дате."""
    grouped = (
        df.groupby("Дата", as_index=False)["Просмотры"]
        .sum()
        .sort_values("Дата")
    )
    return grouped


def top_videos_by_likes(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Топ-N видео по лайкам (для гистограммы)."""
    return df.nlargest(n, "Лайки")[["Название", "Лайки", "Просмотры"]].reset_index(drop=True)
