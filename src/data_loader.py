"""Загрузка и валидация CSV со статистикой видео."""

from __future__ import annotations

import pandas as pd

# Обязательные колонки входного файла.
REQUIRED_COLUMNS = ["Дата", "Название", "Просмотры", "Лайки", "Комментарии"]

# Числовые колонки, которые приводим к int (некорректные -> NaN -> 0).
NUMERIC_COLUMNS = ["Просмотры", "Лайки", "Комментарии"]


class DataValidationError(ValueError):
    """Ошибка валидации входных данных (понятное сообщение для UI)."""


def load_csv(file) -> pd.DataFrame:
    """Читаем CSV с автоопределением разделителя и гибким парсингом даты.

    Параметры
    ---------
    file : file-like
        Объект из st.file_uploader.

    Возвращает
    ----------
    pd.DataFrame
        Очищенный датафрейм с нормализованными типами.
    """
    try:
        # sep=None + engine="python" -> pandas сам угадывает ',' или ';'.
        df = pd.read_csv(file, sep=None, engine="python")
    except Exception as exc:  # noqa: BLE001 - пробрасываем понятную ошибку
        raise DataValidationError(f"Не удалось прочитать CSV: {exc}") from exc

    return _validate_and_normalize(df)


def _validate_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Проверяем колонки и приводим типы данных."""
    # Убираем случайные пробелы в названиях колонок.
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(
            "В файле не хватает колонок: " + ", ".join(missing)
        )

    # Гибкий парсинг даты: понимает и дд.мм.гггг, и ISO.
    df["Дата"] = pd.to_datetime(
        df["Дата"], format="mixed", dayfirst=True, errors="coerce"
    )

    # Числовые поля: приводим к числам, пустые значения -> 0.
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Отбрасываем строки без валидной даты и сортируем по времени.
    df = df.dropna(subset=["Дата"]).sort_values("Дата").reset_index(drop=True)

    if df.empty:
        raise DataValidationError("После обработки не осталось ни одной валидной строки.")

    return df
