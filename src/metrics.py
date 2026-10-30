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


def _pct_change(old: float, new: float) -> float | None:
    """Изменение в процентах. None, если база сравнения равна нулю."""
    if old == 0:
        return None
    return (new - old) / old * 100.0


def _er_mean(part: pd.DataFrame) -> float:
    """Средний ER по части данных (просмотры == 0 не учитываются)."""
    views = part["Просмотры"].astype(float).where(part["Просмотры"] != 0)
    engagements = (part["Лайки"] + part["Комментарии"]).astype(float)
    er_series = (engagements / views * 100).dropna()
    return float(er_series.mean()) if not er_series.empty else 0.0


def compute_trends(df: pd.DataFrame) -> dict[str, float | None]:
    """Изменение KPI между второй и первой половиной периода, в процентах.

    Данные сортируются по дате и делятся пополам по медианной дате (с запасным
    делением по количеству записей). Если половины пусты или база сравнения
    нулевая — соответствующее значение равно None.
    """
    empty = {"videos": None, "views": None, "er": None}
    if len(df) < 2:
        return empty

    ordered = df.sort_values("Дата").reset_index(drop=True)
    cutoff = ordered["Дата"].median()
    first = ordered[ordered["Дата"] <= cutoff]
    second = ordered[ordered["Дата"] > cutoff]
    if first.empty or second.empty:
        mid = len(ordered) // 2
        first, second = ordered.iloc[:mid], ordered.iloc[mid:]
    if first.empty or second.empty:
        return empty

    return {
        "videos": _pct_change(len(first), len(second)),
        "views": _pct_change(
            int(first["Просмотры"].sum()), int(second["Просмотры"].sum())
        ),
        "er": _pct_change(_er_mean(first), _er_mean(second)),
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
