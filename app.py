"""Точка входа Streamlit-дашборда аналитики контента (TikTok/YouTube).

Источник данных — статистика канала из YouTube Data API (после входа через
Google) либо ручная загрузка CSV.
"""

from __future__ import annotations

import streamlit as st

import src.theme as ui
from src import auth
from src.auth.oauth import get_valid_access_token
from src.charts import top_videos_bar_chart, views_line_chart
from src.data_loader import DataValidationError, load_csv
from src.db import init_db
from src.metrics import compute_kpis, top_videos_by_likes, views_by_date
from src.youtube import YouTubeAPIError, fetch_channel_videos, videos_to_dataframe

# --- Настройка страницы: широкий layout и заголовок вкладки ---
st.set_page_config(
    page_title="Content Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- Инициализация хранилища и обработка возврата от Google (?code=...) ---
init_db()
auth.handle_oauth_callback()

user = auth.current_user()

# --- Тема: переключатель в сайдбаре + инъекция стилей ---
with st.sidebar:
    selected_theme = ui.render_theme_toggle()

ui.inject_css(selected_theme)

# --- Шапка страницы ---
ui.hero(
    "📊 Content Analytics Dashboard",
    "Аналитика контента: статистика YouTube-канала или загруженный CSV.",
    badge=st.session_state.get("channel_title"),
)


def render_empty_state() -> None:
    """Подсказка, пока нет данных для анализа."""
    if not user:
        st.info("👈 Войдите через Google/YouTube в боковой панели или загрузите CSV.")
    else:
        st.info("👈 Загрузите статистику из YouTube или CSV-файл в боковой панели.")
    with st.expander("Ожидаемые колонки в CSV-файле"):
        st.markdown(
            "Поддерживаются русские и английские названия колонок:\n\n"
            "- **Дата** / `Date` — дата публикации (дд.мм.гггг или ISO)\n"
            "- **Просмотры** / `Video Views` — количество просмотров\n"
            "- **Лайки** / `Likes` — количество лайков\n"
            "- **Комментарии** / `Comments` — количество комментариев\n"
            "- **Название** / `Title` — название видео (необязательно;\n"
            "  если колонки нет, создаётся автоматически из даты)"
        )


def load_youtube_data() -> None:
    """Выгрузить статистику канала и положить результат в session_state."""
    token = get_valid_access_token(user["id"])
    if not token:
        st.session_state["youtube_error"] = (
            "Нет действующего токена доступа. Войдите заново."
        )
        return

    try:
        with st.spinner("Загружаем статистику канала…"):
            channel, videos = fetch_channel_videos(token, max_videos=50)
            df_yt = videos_to_dataframe(videos)
    except YouTubeAPIError as exc:
        st.session_state["youtube_error"] = str(exc)
        return
    except Exception as exc:  # noqa: BLE001
        st.session_state["youtube_error"] = f"Ошибка выгрузки: {exc}"
        return

    if df_yt.empty:
        st.session_state["youtube_error"] = "На канале не найдено видео."
        return

    st.session_state["df_youtube"] = df_yt
    st.session_state["channel_title"] = (
        channel.get("snippet", {}).get("title") or "Ваш канал"
    )
    st.session_state.pop("youtube_error", None)


# --- Боковая панель: аккаунт и источник данных ---
with st.sidebar:
    st.divider()
    st.header("👤 Аккаунт")
    if user:
        if user.get("picture"):
            st.image(user["picture"], width=64)
        st.write(f"**{user.get('name') or 'Пользователь'}**")
        if user.get("email"):
            st.caption(user["email"])
        if st.button("Выйти", width="stretch"):
            auth.logout()
            st.session_state.pop("df_youtube", None)
            st.rerun()
    else:
        if st.button("Войти через Google / YouTube", width="stretch"):
            auth.login()

    if error := st.session_state.get("auth_error"):
        st.error(error)

    st.divider()
    st.header("📁 Данные")
    source = st.radio(
        "Источник данных",
        ["YouTube (авто)", "CSV-файл"],
        index=0 if user else 1,
    )

    uploaded = None
    if source == "YouTube (авто)":
        if not user:
            st.info("Войдите, чтобы загрузить статистику канала.")
        else:
            if st.button("⬇️ Загрузить статистику канала", width="stretch"):
                load_youtube_data()
            if error := st.session_state.get("youtube_error"):
                st.error(error)
    else:
        uploaded = st.file_uploader("CSV-файл со статистикой", type=["csv"])

# --- Определяем данные для анализа ---
df = None

if uploaded is not None:
    try:
        df = load_csv(uploaded)
    except DataValidationError as exc:
        st.error(f"Ошибка в данных: {exc}")
        st.stop()
elif source == "YouTube (авто)":
    df = st.session_state.get("df_youtube")
    if df is None:
        render_empty_state()
        ui.footer("Content Analytics Dashboard · данные YouTube или CSV")
        st.stop()

if df is None:
    render_empty_state()
    ui.footer("Content Analytics Dashboard · данные YouTube или CSV")
    st.stop()

# --- Контекст: что за канал/источник сейчас показан ---
if source == "YouTube (авто)" and st.session_state.get("channel_title"):
    st.caption(f"Канал: **{st.session_state['channel_title']}**")

# --- Расчёт метрик ---
kpis = compute_kpis(df)
views_df = views_by_date(df)
top_df = top_videos_by_likes(df, n=5)

# --- Ряд 1: KPI-карточки в три колонки ---
col1, col2, col3 = st.columns(3)
with col1:
    ui.kpi_card("🎬", f"{kpis['n_videos']:,}".replace(",", " "), "Всего видео")
with col2:
    ui.kpi_card(
        "👁️", f"{kpis['total_views']:,}".replace(",", " "), "Суммарные просмотры"
    )
with col3:
    ui.kpi_card("❤️", f"{kpis['avg_er']:.2f} %", "Средний ER")

# --- Ряд 2: вкладки Обзор / Данные ---
tab_overview, tab_data = st.tabs(["📈 Обзор", "📋 Данные"])

with tab_overview:
    st.plotly_chart(
        views_line_chart(views_df, selected_theme), width="stretch"
    )
    st.plotly_chart(
        top_videos_bar_chart(top_df, selected_theme), width="stretch"
    )

with tab_data:
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Дата": st.column_config.DateColumn("Дата", format="DD.MM.YYYY"),
            "Просмотры": st.column_config.NumberColumn("Просмотры", format="%d"),
            "Лайки": st.column_config.NumberColumn("Лайки", format="%d"),
            "Комментарии": st.column_config.NumberColumn(
                "Комментарии", format="%d"
            ),
            "Название": st.column_config.TextColumn("Название", width="large"),
        },
    )

ui.footer("Content Analytics Dashboard · данные YouTube или CSV")
