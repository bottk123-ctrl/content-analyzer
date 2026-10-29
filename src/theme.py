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
    "gradient": "linear-gradient(135deg, #4F8BF9 0%, #7C5CFF 100%)",
    "plotly_template": "plotly_white",
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
    "gradient": "linear-gradient(135deg, #2563EB 0%, #7C5CFF 100%)",
    "plotly_template": "plotly_dark",
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
            --ca-gradient: {p['gradient']};

            --background-color: {p['bg']};
            --secondary-background-color: {p['panel']};
            --text-color: {p['text']};
            --primary-color: {p['primary']};
        }}

        html, body, .stApp, [class*="st-"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background: var(--ca-bg); color: var(--ca-text); }}

        /* Убираем дефолтный футер и меню для чистого вида */
        #MainMenu, footer {{ visibility: hidden; }}

        /* Hero-баннер */
        .ca-hero {{
            background: var(--ca-gradient);
            border-radius: 18px;
            padding: 30px 34px;
            color: #fff;
            margin: 4px 0 10px;
            box-shadow: 0 12px 32px rgba(79,139,249,.28);
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
            border-radius: 16px;
            padding: 20px 22px 18px;
            box-shadow: var(--ca-shadow);
            height: 100%;
        }}
        .ca-kpi::before {{
            content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
            background: var(--ca-gradient);
        }}
        .ca-kpi .ca-kpi-icon {{ font-size: 1.35rem; }}
        .ca-kpi .ca-kpi-value {{
            font-size: 1.9rem; font-weight: 800; color: var(--ca-text);
            line-height: 1.2; margin-top: 4px;
        }}
        .ca-kpi .ca-kpi-label {{
            font-size: .78rem; color: var(--ca-muted);
            text-transform: uppercase; letter-spacing: .05em; margin-top: 2px;
        }}

        /* Вкладки */
        .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 10px 10px 0 0; padding: 8px 16px; font-weight: 600;
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


def kpi_card(icon: str, value: str, label: str) -> None:
    """Карточка ключевого показателя."""
    st.markdown(
        f'<div class="ca-kpi"><div class="ca-kpi-icon">{icon}</div>'
        f'<div class="ca-kpi-value">{value}</div>'
        f'<div class="ca-kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def footer(text: str) -> None:
    """Аккуратный футер."""
    st.markdown(f'<div class="ca-footer">{text}</div>', unsafe_allow_html=True)
