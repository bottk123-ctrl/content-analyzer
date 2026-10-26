"""Управление текущим пользователем в рамках Streamlit-сессии."""

from __future__ import annotations

import streamlit as st

from . import oauth

_USER_KEY = "auth_user"


def current_user() -> dict | None:
    """Данные текущего пользователя или None, если он не вошёл."""
    return st.session_state.get(_USER_KEY)


def is_logged_in() -> bool:
    return current_user() is not None


def handle_oauth_callback() -> None:
    """Обработать возврат от Google (?code=...&state=...) и завершить вход.

    Вызывается в начале каждого прогона скрипта. Если параметров нет —
    просто ничего не делает.
    """
    params = st.query_params
    code = params.get("code")
    if not code:
        return

    state = params.get("state")
    try:
        user = oauth.complete_login(code=code, state=state)
    except oauth.OAuthError as exc:
        st.session_state["auth_error"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        st.session_state["auth_error"] = f"Не удалось завершить вход: {exc}"
    else:
        st.session_state[_USER_KEY] = user
        st.session_state.pop("auth_error", None)
    finally:
        _clear_query_params()


def login() -> None:
    """Инициировать вход: сформировать URL и перенаправить браузер."""
    try:
        url = oauth.build_authorization_url()
    except oauth.OAuthError as exc:
        st.session_state["auth_error"] = str(exc)
        return
    _redirect(url)


def logout() -> None:
    st.session_state.pop(_USER_KEY, None)
    st.session_state.pop("auth_error", None)


def _clear_query_params() -> None:
    try:
        st.query_params.clear()
    except Exception:  # noqa: BLE001
        pass


def _redirect(url: str) -> None:
    """Редирект на внешний URL.

    Meta-refresh в большинстве браузеров срабатывает сразу; кнопка-ссылка
    остаётся запасным вариантом, если браузер его проигнорирует.
    """
    st.markdown(
        f'<meta http-equiv="refresh" content="0; url={url}">',
        unsafe_allow_html=True,
    )
    st.info("Перенаправляем на страницу входа Google…")
    st.link_button("Продолжить вход через Google", url)
    st.stop()
