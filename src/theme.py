"""Единая визуальная тема дашборда: палитры, CSS, переключатель, компоненты.

Streamlit задаёт тему только при старте через config.toml, поэтому смену
темы на лету делаем переопределением CSS-переменных Streamlit и собственных
переменных ``--ca-*`` для кастомных компонентов (hero, карточки KPI).
"""

from __future__ import annotations

import streamlit as st

LIGHT = {
    "bg": "#FFFFFF",
    "panel": "#F4F7FB",
    "text": "#1B1F24",
    "muted": "#5B6470",
    "primary": "#4F8BF9",
    "border": "#E4E9F0",
    "card": "#FFFFFF",
    "grid": "rgba(27,31,36,0.08)",
    "shadow": "0 1px 3px rgba(16,24,40,.06), 0 1px 2px rgba(16,24,40,.05)",
    "shadow_hover": "0 14px 30px rgba(16,24,40,.14), 0 4px 10px rgba(16,24,40,.08)",
    "gradient": "linear-gradient(135deg, #4F8BF9 0%, #7C5CFF 100%)",
    "plotly_template": "plotly_white",
    "positive": "#16A34A",
    "negative": "#DC2626",
    "positive_bg": "#E7F7EC",
    "negative_bg": "#FDECEC",
    "chip_bg": "#EAF1FE",
    "chip_fg": "#3B6FE0",
    "chip_ring": "rgba(79,139,249,.22)",
}

DARK = {
    "bg": "#0E1117",
    "panel": "#161B22",
    "text": "#E6EDF3",
    "muted": "#9AA4B2",
    "primary": "#6EA8FE",
    "border": "#2A313C",
    "card": "#161B22",
    "grid": "rgba(230,237,243,0.10)",
    "shadow": "0 1px 3px rgba(0,0,0,.5), 0 1px 2px rgba(0,0,0,.4)",
    "shadow_hover": "0 16px 34px rgba(0,0,0,.62), 0 4px 12px rgba(0,0,0,.5)",
    "gradient": "linear-gradient(135deg, #2563EB 0%, #7C5CFF 100%)",
    "plotly_template": "plotly_dark",
    "positive": "#3FB950",
    "negative": "#F85149",
    "positive_bg": "rgba(63,185,80,.16)",
    "negative_bg": "rgba(248,81,73,.16)",
    "chip_bg": "rgba(110,168,254,.16)",
    "chip_fg": "#9CC0FF",
    "chip_ring": "rgba(110,168,254,.30)",
}

PALETTES = {"light": LIGHT, "dark": DARK}

_THEME_KEY = "theme"
_CHOICE_KEY = "theme_choice"
_LIGHT_LABEL = "☀️ Светлая"
_DARK_LABEL = "🌙 Тёмная"


def get_palette(theme: str) -> dict:
    """Палитра по имени темы (неизвестная -> светлая)."""
    return PALETTES.get(theme, LIGHT)


def current_theme() -> str:
    """Текущая тема из session_state (по умолчанию светлая)."""
    return st.session_state.get(_THEME_KEY, "light")


def render_theme_toggle() -> str:
    """Переключатель темы для сайдбара. Возвращает выбранную тему."""
    st.session_state.setdefault(_THEME_KEY, "light")
    labels = [_LIGHT_LABEL, _DARK_LABEL]
    st.session_state.setdefault(
        _CHOICE_KEY, labels[1] if current_theme() == "dark" else labels[0]
    )

    choice = st.segmented_control(
        "Тема оформления", labels, key=_CHOICE_KEY, label_visibility="collapsed"
    )
    theme = "dark" if choice == _DARK_LABEL else "light"
    st.session_state[_THEME_KEY] = theme
    return theme


def inject_css(theme: str) -> None:
    """Внедряем CSS-переменные и стили компонентов под выбранную тему."""
    p = get_palette(theme)

    # Правки, которые нужны только в тёмной теме: у некоторых кнопок Streamlit
    # фон остаётся светлым, поэтому принудительно делаем текст тёмным.
    dark_rules = ""
    if theme == "dark":
        dark_rules = """
        [data-testid="stFileUploaderDropzone"] button,
        [data-testid="stFileUploaderDropzone"] button * {
            color: #111111 !important;
        }
        """

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root, .stApp {{
            --ca-bg: {p['bg']};
            --ca-panel: {p['panel']};
            --ca-text: {p['text']};
            --ca-muted: {p['muted']};
            --ca-primary: {p['primary']};
            --ca-border: {p['border']};
            --ca-card: {p['card']};
            --ca-grid: {p['grid']};
            --ca-shadow: {p['shadow']};
            --ca-shadow-hover: {p['shadow_hover']};
            --ca-gradient: {p['gradient']};
            --ca-positive: {p['positive']};
            --ca-negative: {p['negative']};
            --ca-positive-bg: {p['positive_bg']};
            --ca-negative-bg: {p['negative_bg']};
            --ca-chip-bg: {p['chip_bg']};
            --ca-chip-fg: {p['chip_fg']};
            --ca-chip-ring: {p['chip_ring']};
            --ca-radius: 16px;

            --background-color: {p['bg']};
            --secondary-background-color: {p['panel']};
            --text-color: {p['text']};
            --primary-color: {p['primary']};
            --sidebar-background-color: {p['bg']};
        }}

        /* Шрифт задаём только контейнерам, НЕ всем [class*="st-"]:
           emotion-классы Streamlit тоже начинаются с "st-", и широкий селектор
           перебивал шрифт иконок Material Symbols (иконки рисовались текстом). */
        html, body, .stApp {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background: var(--ca-bg); color: var(--ca-text); }}

        @keyframes ca-fade-up {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Боковая панель: фон и текст под текущую тему */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"] {{
            background: var(--ca-bg);
            color: var(--ca-text);
        }}
        [data-testid="stSidebar"] {{
            border-right: 1px solid var(--ca-border);
        }}
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4 {{
            color: var(--ca-text);
        }}

        /* Верхняя шапка: прозрачная, чтобы не было белой полосы */
        header[data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stToolbar"] {{ background: transparent; }}

        /* Файлоаплоадер: тёмная зона загрузки и читаемый текст */
        [data-testid="stFileUploader"] section,
        [data-testid="stFileUploaderDropzone"] {{
            background: var(--ca-panel);
            border: 1px dashed var(--ca-border);
            color: var(--ca-text);
        }}
        [data-testid="stFileUploaderDropzone"] *,
        [data-testid="stFileUploader"] span,
        [data-testid="stFileUploader"] small {{
            color: var(--ca-text);
        }}
        [data-testid="stFileUploader"] small {{ color: var(--ca-muted); }}

        /* Чип загруженного файла: фон и текст под текущую тему
           (по умолчанию фон светлый и текст становится нечитаемым). */
        [data-testid="stFileChip"] {{
            background: var(--ca-card) !important;
            border: 1px solid var(--ca-border) !important;
            color: var(--ca-text) !important;
        }}
        [data-testid="stFileChip"] * {{ color: var(--ca-text) !important; }}
        [data-testid="stFileChip"] svg {{ fill: var(--ca-muted); }}

        /* Кнопки в сайдбаре: тёмный фон, рамка и текст под тему */
        [data-testid="stSidebar"] .stButton > button {{
            background: var(--ca-panel);
            color: var(--ca-text);
            border: 1px solid var(--ca-border);
            transition: border-color .18s ease, color .18s ease, transform .18s ease;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            border-color: var(--ca-primary);
            color: var(--ca-primary);
            transform: translateY(-1px);
        }}

        /* Переключатель темы: сегмент-контрол (stButtonGroup).
           В актуальных версиях Streamlit segmented_control рендерится как
           stButtonGroup с кнопками role="radio", а не stSegmentedControl. */
        [data-testid="stButtonGroup"] [role="radiogroup"] {{
            background: var(--ca-panel);
            border: 1px solid var(--ca-border);
            border-radius: 999px;
            padding: 3px;
            gap: 3px;
        }}
        [data-testid="stButtonGroup"] [role="radiogroup"] button {{
            border: 1px solid transparent !important;
            border-radius: 999px !important;
            background: transparent !important;
            color: var(--ca-muted) !important;
            transition: background .18s ease, color .18s ease, box-shadow .18s ease;
        }}
        [data-testid="stButtonGroup"] [role="radiogroup"] button[aria-checked="true"] {{
            background: var(--ca-card) !important;
            color: var(--ca-primary) !important;
            border-color: var(--ca-chip-ring) !important;
            box-shadow: var(--ca-shadow);
        }}

        /* Явно сохраняем шрифт иконок Material Symbols */
        [data-testid="stIconMaterial"],
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons {{
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                'Material Icons' !important;
        }}

        /* Убираем дефолтный футер и меню для чистого вида */
        #MainMenu, footer {{ visibility: hidden; }}

        /* Карточки-контейнеры (st.container(border=True, key="ca-card-...")).
           Класс st-key-<key> стабильнее, чем data-testid из внутренностей
           Streamlit, и не ломается при обновлениях версии. */
        [class*="st-key-ca-card"] {{
            background: var(--ca-card);
            border: 1px solid var(--ca-border) !important;
            border-radius: var(--ca-radius);
            box-shadow: var(--ca-shadow);
            transition: box-shadow .18s ease, border-color .18s ease;
        }}
        [class*="st-key-ca-card"]:hover {{
            box-shadow: var(--ca-shadow-hover);
            border-color: var(--ca-chip-ring) !important;
        }}

        /* Заголовок секции внутри карточки */
        .ca-section-title {{
            display: flex; align-items: center; gap: 8px;
            font-size: 1.05rem; font-weight: 700; color: var(--ca-text);
            letter-spacing: -.01em; margin: 2px 0 4px;
        }}

        /* Отступы и скругления для st.expander */
        [data-testid="stExpander"] {{
            margin: 8px 0 16px;
            border: 1px solid var(--ca-border);
            border-radius: 12px;
            overflow: hidden;
        }}
        [data-testid="stExpander"] summary {{
            padding: 10px 14px;
            line-height: 1.45;
        }}
        [data-testid="stExpander"] summary p {{ margin: 0; }}
        [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
            padding: 4px 16px 12px;
        }}

        /* Hero-баннер */
        .ca-hero {{
            position: relative; overflow: hidden;
            background: var(--ca-gradient);
            border-radius: 18px;
            padding: 32px 36px;
            color: #fff;
            margin: 4px 0 12px;
            box-shadow: 0 16px 38px rgba(79,139,249,.30);
            animation: ca-fade-up .5s ease both;
        }}
        .ca-hero::after {{
            content: ""; position: absolute; right: -70px; top: -70px;
            width: 260px; height: 260px; border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,.22), rgba(255,255,255,0) 70%);
            pointer-events: none;
        }}
        .ca-hero h1 {{ margin: 0; font-size: 2rem; font-weight: 800; color: #fff; }}
        .ca-hero p {{ margin: 8px 0 0; font-size: .96rem; opacity: .94; }}
        .ca-hero .ca-hero-badge {{
            display: inline-block; margin-top: 12px; padding: 4px 12px;
            background: rgba(255,255,255,.18); border-radius: 999px;
            font-size: .82rem; font-weight: 600;
        }}

        /* KPI-карточки */
        .ca-kpi {{
            position: relative; overflow: hidden;
            background: var(--ca-card);
            border: 1px solid var(--ca-border);
            border-radius: var(--ca-radius);
            padding: 20px 22px 18px;
            box-shadow: var(--ca-shadow);
            height: 100%;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
            animation: ca-fade-up .5s ease both;
        }}
        .ca-kpi:hover {{
            transform: translateY(-4px);
            box-shadow: var(--ca-shadow-hover);
            border-color: var(--ca-chip-ring);
        }}
        .ca-kpi::before {{
            content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
            background: var(--ca-gradient);
        }}
        .ca-kpi .ca-kpi-top {{
            display: flex; align-items: center; justify-content: space-between;
            gap: 10px;
        }}
        .ca-kpi .ca-kpi-icon {{
            width: 42px; height: 42px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.35rem;
            background: var(--ca-chip-bg);
            box-shadow: inset 0 0 0 1px var(--ca-chip-ring);
        }}
        .ca-kpi .ca-kpi-delta {{
            font-size: .78rem; font-weight: 700; padding: 3px 9px;
            border-radius: 999px; white-space: nowrap;
        }}
        .ca-kpi .ca-kpi-delta.up {{ color: var(--ca-positive); background: var(--ca-positive-bg); }}
        .ca-kpi .ca-kpi-delta.down {{ color: var(--ca-negative); background: var(--ca-negative-bg); }}
        .ca-kpi .ca-kpi-delta.flat {{ color: var(--ca-muted); background: var(--ca-panel); }}
        .ca-kpi .ca-kpi-value {{
            font-size: 2.05rem; font-weight: 800; color: var(--ca-text);
            line-height: 1.15; margin-top: 12px; letter-spacing: -.01em;
        }}
        .ca-kpi .ca-kpi-label {{
            font-size: .78rem; color: var(--ca-muted);
            text-transform: uppercase; letter-spacing: .06em; margin-top: 4px;
        }}

        /* Пустое состояние */
        .ca-empty {{
            text-align: center; padding: 42px 24px;
            background: var(--ca-panel);
            border: 1px dashed var(--ca-border);
            border-radius: 18px;
            margin: 6px 0 16px;
            animation: ca-fade-up .5s ease both;
        }}
        .ca-empty .ca-empty-icon {{ font-size: 2.6rem; line-height: 1; }}
        .ca-empty h3 {{
            margin: 12px 0 4px; font-size: 1.18rem;
            font-weight: 700; color: var(--ca-text);
        }}
        .ca-empty p {{ margin: 0; color: var(--ca-muted); font-size: .93rem; }}

        /* Вкладки */
        .stTabs [data-baseweb="tab-list"],
        [data-testid="stTabs"] [role="tablist"] {{
            gap: 6px; border-bottom: 1px solid var(--ca-border);
        }}
        .stTabs [data-baseweb="tab"],
        [data-testid="stTab"] {{
            border-radius: 10px 10px 0 0; padding: 8px 18px; font-weight: 600;
            color: var(--ca-muted);
        }}
        .stTabs [aria-selected="true"],
        [data-testid="stTab"][aria-selected="true"] {{
            color: var(--ca-primary);
        }}

        /* Кнопки */
        .stButton > button, .stDownloadButton > button {{
            border-radius: 10px; font-weight: 600;
        }}

        /* Футер */
        .ca-footer {{
            margin-top: 28px; padding-top: 14px;
            border-top: 1px solid var(--ca-border);
            color: var(--ca-muted); font-size: .82rem; text-align: center;
        }}

        @media (prefers-reduced-motion: reduce) {{
            .ca-hero, .ca-kpi, .ca-empty {{ animation: none; }}
            .ca-kpi {{ transition: none; }}
        }}

        {dark_rules}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badge: str | None = None) -> None:
    """Градиентная шапка страницы."""
    badge_html = f'<div class="ca-hero-badge">{badge}</div>' if badge else ""
    st.markdown(
        f'<div class="ca-hero"><h1>{title}</h1>'
        f"<p>{subtitle}</p>{badge_html}</div>",
        unsafe_allow_html=True,
    )


def kpi_card(
    icon: str, value: str, label: str, delta: float | None = None
) -> None:
    """Карточка ключевого показателя с опциональным бейджем тренда.

    ``delta`` — изменение в процентах; None скрывает бейдж.
    """
    delta_html = ""
    if delta is not None:
        if delta > 0.05:
            cls, arrow, sign = "up", "▲", "+"
        elif delta < -0.05:
            cls, arrow, sign = "down", "▼", ""
        else:
            cls, arrow, sign = "flat", "■", ""
        delta_html = (
            f'<div class="ca-kpi-delta {cls}">{arrow} {sign}{delta:.1f}%</div>'
        )

    st.markdown(
        f'<div class="ca-kpi"><div class="ca-kpi-top">'
        f'<div class="ca-kpi-icon">{icon}</div>{delta_html}</div>'
        f'<div class="ca-kpi-value">{value}</div>'
        f'<div class="ca-kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    """Заголовок секции внутри карточки."""
    st.markdown(f'<div class="ca-section-title">{text}</div>', unsafe_allow_html=True)


def empty_state(icon: str, title: str, hint: str) -> None:
    """Стилизованный блок пустого состояния."""
    st.markdown(
        f'<div class="ca-empty"><div class="ca-empty-icon">{icon}</div>'
        f"<h3>{title}</h3><p>{hint}</p></div>",
        unsafe_allow_html=True,
    )


def footer(text: str) -> None:
    """Аккуратный футер."""
    st.markdown(f'<div class="ca-footer">{text}</div>', unsafe_allow_html=True)
