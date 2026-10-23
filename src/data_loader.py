"""Загрузка и валидация CSV со статистикой видео."""

from __future__ import annotations

import io
import re

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

# Русские названия месяцев (включая родительный падеж и сокращения) -> число.
# Нужны, потому что pandas не понимает даты вида "15 октября 2026".
_RU_MONTHS = {
    "января": 1, "январь": 1, "янв": 1,
    "февраля": 2, "февраль": 2, "фев": 2, "февр": 2,
    "марта": 3, "март": 3, "мар": 3,
    "апреля": 4, "апрель": 4, "апр": 4,
    "мая": 5, "май": 5,
    "июня": 6, "июнь": 6, "июн": 6,
    "июля": 7, "июль": 7, "июл": 7,
    "августа": 8, "август": 8, "авг": 8,
    "сентября": 9, "сентябрь": 9, "сент": 9, "сен": 9,
    "октября": 10, "октябрь": 10, "окт": 10,
    "ноября": 11, "ноябрь": 11, "ноя": 11,
    "декабря": 12, "декабрь": 12, "дек": 12,
}

# Регулярное выражение со всеми формами месяцев (длинные — вперёд, чтобы
# "марта" не превращалось в "мар" + "та"). \b работает с кириллицей.
_RU_MONTH_REGEX = re.compile(
    r"\b(?:" + "|".join(sorted(_RU_MONTHS, key=len, reverse=True)) + r")\b",
    flags=re.IGNORECASE,
)


class DataValidationError(ValueError):
    """Ошибка валидации входных данных (понятное сообщение для UI)."""


def load_csv(file) -> pd.DataFrame:
    """Читаем CSV с автоопределением разделителя, кодировки и парсингом даты.

    Параметры
    ---------
    file : file-like
        Объект из st.file_uploader.

    Возвращает
    ----------
    pd.DataFrame
        Очищенный датафрейм с нормализованными типами.
    """
    df = _read_csv(file)
    return _validate_and_normalize(df)


def _read_csv(file) -> pd.DataFrame:
    """Читаем CSV, декодируя байты вручную (BOM/CP1251/UTF-8).

    Мы сами декодируем содержимое, чтобы не зависеть от режима открытия
    файла (бинарный поток из Streamlit vs текстовый) и корректно снять BOM.
    """
    try:
        raw = file.read() if hasattr(file, "read") else file
    except Exception as exc:  # noqa: BLE001
        raise DataValidationError(f"Не удалось прочитать файл: {exc}") from exc

    # Если пришла уже строка — используем как есть.
    if isinstance(raw, str):
        text = raw
    else:
        text = None
        last_error: Exception | None = None
        # utf-8-sig первым — он снимает BOM (\ufeff) с первого заголовка.
        for encoding in ("utf-8-sig", "cp1251", "utf-8"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
        if text is None:
            raise DataValidationError(
                f"Не удалось определить кодировку файла: {last_error}"
            )

    try:
        # sep=None + engine="python" -> pandas сам угадывает ',' или ';'.
        return pd.read_csv(io.StringIO(text), sep=None, engine="python")
    except Exception as exc:  # noqa: BLE001 - пробрасываем понятную ошибку
        raise DataValidationError(f"Не удалось прочитать CSV: {exc}") from exc


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Чистим заголовки: убираем BOM, кавычки, пробелы и лишние разделители."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)   # BOM
        .str.replace('"', "", regex=False)         # двойные кавычки
        .str.replace("'", "", regex=False)         # одинарные кавычки
        .str.strip()
    )
    return df


def _normalize_key(name: str) -> str:
    """Нормализуем имя колонки для поиска в маппинге."""
    cleaned = (
        str(name)
        .replace("\ufeff", "")
        .replace('"', "")
        .replace("'", "")
        .strip()
        .lower()
    )
    # Склеиваем повторяющиеся пробелы в один.
    return " ".join(cleaned.split())


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Переводим известные колонки во внутренние (регистро/пробел-независимо)."""
    df = df.rename(columns=lambda col: COLUMN_MAPPING.get(_normalize_key(col), col))
    # Если несколько исходных колонок схлопнулись в одну — оставляем первую.
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _parse_dates(series: pd.Series) -> pd.Series:
    """Парсим даты: поддерживаем ISO, дд.мм.гггг и русские месяцы."""
    text = series.astype(str).str.strip()

    # "15 октября 2026" -> "15 10 2026", "окт" -> "10" и т.п.
    def _replace_month(match: re.Match) -> str:
        return str(_RU_MONTHS[match.group(0).lower()])

    text = text.str.replace(_RU_MONTH_REGEX, _replace_month, regex=True)

    # Разделители (точки, слэши, запятые, лишние пробелы) -> единый пробел,
    # чтобы pandas корректно разобрал компоненты даты с dayfirst=True.
    text = text.str.replace(r"[.,/\\]+", " ", regex=True)
    text = text.str.replace(r"\s+", " ", regex=True).str.strip()

    return pd.to_datetime(text, format="mixed", dayfirst=True, errors="coerce")


def _validate_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Проверяем колонки, синтезируем недостающие и приводим типы данных."""
    df = _clean_columns(df)
    df = _rename_columns(df)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(
            "В файле не хватает колонок: " + ", ".join(missing)
        )

    # Гибкий парсинг даты: ISO, дд.мм.гггг и русские месяцы.
    df["Дата"] = _parse_dates(df["Дата"])

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
