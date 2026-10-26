"""Преобразование ответов YouTube API во внутренний формат дашборда.

Итоговый DataFrame повторяет схему, которую выдаёт ``src.data_loader.load_csv``,
поэтому метрики и графики переиспользуются без изменений.
"""

from __future__ import annotations

import pandas as pd

INTERNAL_COLUMNS = ["Дата", "Просмотры", "Лайки", "Комментарии", "Название"]


def _to_int(value) -> int:
    """Строку/None из API -> int (некорректное -> 0)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def videos_to_dataframe(items: list[dict]) -> pd.DataFrame:
    """Список ресурсов ``video`` -> нормализованный DataFrame.

    Соответствие полей YouTube -> внутренняя схема:
        snippet.publishedAt -> Дата
        snippet.title       -> Название
        statistics.viewCount    -> Просмотры
        statistics.likeCount    -> Лайки
        statistics.commentCount -> Комментарии
    """
    rows = []
    for item in items:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        rows.append(
            {
                "Дата": snippet.get("publishedAt"),
                "Название": snippet.get("title") or "Без названия",
                "Просмотры": _to_int(stats.get("viewCount")),
                "Лайки": _to_int(stats.get("likeCount")),
                "Комментарии": _to_int(stats.get("commentCount")),
            }
        )

    df = pd.DataFrame(rows, columns=INTERNAL_COLUMNS)
    if df.empty:
        return df

    # publishedAt в ISO 8601 (UTC) -> naive datetime, как ждёт остальной код.
    df["Дата"] = pd.to_datetime(df["Дата"], errors="coerce", utc=True).dt.tz_localize(
        None
    )
    for col in ("Просмотры", "Лайки", "Комментарии"):
        df[col] = df[col].astype(int)

    return (
        df.dropna(subset=["Дата"])
        .sort_values("Дата")
        .reset_index(drop=True)
    )
