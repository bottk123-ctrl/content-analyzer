"""Загрузка и валидация CSV со статистикой видео."""

from __future__ import annotations

import pandas as pd

# Обязательные колонки (внутренние имена). "Название" — необязательная:
# если её нет в файле, мы синтезируем её из даты.
REQUIRED_COLUMNS = ["Дата", "Просмотры", "Лайки", "Комментарии"]

# Числовые колонки, которые приводим к int (некорректные -> NaN -> 0).
NUMERIC_COLUMNS = ["Просмотры", "Лайки", "Комментарии"]

# Словарь-переводчик: ключ — нормализованное (lower/strip) имя из файла,
# значение — внутреннее имя, которое использует всё приложение.
# Поддерживаем и английские выгрузки (например, TikTok Studio), и русские.
COLUMN_MAPPING = {
    # Дата
    "дата": "Дата",
    "date": "Дата",
    # Просмотры
    "просмотры": "Просмотры",
    "video views": "Просмотры",
    "views": "Просмотры",
    # Лайки
    "лайки": "Лайки",
    "likes": "Лайки",
    # Комментарии
    "комментарии": "Комментарии",
    "comments": "Комментарии",
    # Название (необязательно)
    "название": "Название",
    "title": "Название",
    "name": "Название",
    "video title": "Название",
    "video name": "Название",
}


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


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Переводим известные колонки во внутренние имена (регистронезависимо)."""
    # Убираем пробелы и переводим известные названия во внутренние.
    df = df.rename(
        columns=lambda col: COLUMN_MAPPING.get(str(col).strip().lower(), str(col).strip())
    )
    # Если несколько исходных колонок схлопнулись в одну — оставляем первую.
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _validate_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Проверяем колонки, синтезируем недостающие и приводим типы данных."""
    df = _rename_columns(df)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(
            "В файле не хватает колонок: " + ", ".join(missing)
        )

    # Гибкий парсинг даты: понимает и дд.мм.гггг, и ISO.
    df["Дата"] = pd.to_datetime(
        df["Дата"], format="mixed", dayfirst=True, errors="coerce"
    )

    # Если колонки "Название" нет (например, в выгрузке TikTok Studio) —
    # создаём её на основе даты, чтобы UI и Топ-5 продолжали работать.
    if "Название" not in df.columns:
        df["Название"] = "Видео от " + df["Дата"].dt.strftime("%d.%m.%Y")

    # Числовые поля: приводим к числам, пустые значения -> 0.
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Отбрасываем строки без валидной даты и сортируем по времени.
    df = df.dropna(subset=["Дата"]).sort_values("Дата").reset_index(drop=True)

    if df.empty:
        raise DataValidationError("После обработки не осталось ни одной валидной строки.")

    return df
