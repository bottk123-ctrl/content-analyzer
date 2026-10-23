"""Точка входа Streamlit-дашборда аналитики контента (TikTok/YouTube)."""

from __future__ import annotations

import streamlit as st

from src.charts import top_videos_bar_chart, views_line_chart
from src.data_loader import DataValidationError, load_csv
from src.metrics import compute_kpis, top_videos_by_likes, views_by_date

# --- Настройка страницы: широкий layout и заголовок вкладки ---
st.set_page_config(
    page_title="Content Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Content Analytics Dashboard")
st.caption("Загрузите CSV со статистикой видео — получите сводные метрики и графики.")


def render_empty_state() -> None:
    """Заглушка, пока файл не загружен."""
    st.info("⬅️ Загрузите CSV-файл в боковой панели, чтобы начать анализ.")
    with st.expander("Ожидаемые колонки в файле"):
        st.markdown(
            "- **Дата** — дата публикации (дд.мм.гггг или ISO)\n"
            "- **Название** — название видео\n"
            "- **Просмотры** — количество просмотров\n"
            "- **Лайки** — количество лайков\n"
            "- **Комментарии** — количество комментариев"
        )


# --- Боковая панель: загрузка файла ---
with st.sidebar:
    st.header("📁 Данные")
    uploaded = st.file_uploader("CSV-файл со статистикой", type=["csv"])

# Если файл не загружен — показываем подсказку и останавливаемся.
if uploaded is None:
    render_empty_state()
    st.stop()

# --- Загрузка и валидация ---
try:
    df = load_csv(uploaded)
except DataValidationError as exc:
    st.error(f"Ошибка в данных: {exc}")
    st.stop()

# --- Расчёт метрик ---
kpis = compute_kpis(df)
views_df = views_by_date(df)
top_df = top_videos_by_likes(df, n=5)

# --- Ряд 1: KPI-карточки в три колонки ---
col1, col2, col3 = st.columns(3)
col1.metric("🎬 Всего видео", f"{kpis['n_videos']:,}".replace(",", " "))
col2.metric("👁️ Суммарные просмотры", f"{kpis['total_views']:,}".replace(",", " "))
col3.metric("❤️ Средний ER", f"{kpis['avg_er']:.2f} %")

st.divider()

# --- Ряд 2: линейный график на всю ширину ---
st.plotly_chart(views_line_chart(views_df), use_container_width=True)

# --- Ряд 3: Топ-5 (слева) и таблица данных (справа) ---
left, right = st.columns([3, 2])
with left:
    st.plotly_chart(top_videos_bar_chart(top_df), use_container_width=True)
with right:
    st.subheader("📋 Все данные")
    st.dataframe(df, use_container_width=True, hide_index=True)
