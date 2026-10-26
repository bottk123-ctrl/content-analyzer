"""OAuth 2.0 поток входа через Google с доступом к YouTube Data API.

Почему свой поток, а не встроенный ``st.login()``: встроенный вариант работает
по OpenID Connect и даёт только *аутентификацию* (кто пользователь), но не
*авторизацию* — у приложения не появляется access token для вызовов YouTube API
от имени пользователя. Нам нужен именно доступ к данным, поэтому реализуем
authorization code flow вручную на Authlib.

Параметр ``state`` (защита от CSRF) хранится в БД: между редиректом на Google
и обратно Streamlit пересоздаёт сессию, и ``st.session_state`` недоступен.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import requests
from authlib.integrations.requests_client import OAuth2Session

from src.db import OAuthState, OAuthToken, User, init_db, session_scope
from src.db.crypto import decrypt, encrypt

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"

DEFAULT_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Сколько живёт выданный state (с запасом на прохождение логина в Google).
_STATE_TTL = timedelta(minutes=15)


class OAuthError(RuntimeError):
    """Ошибка OAuth-потока с понятным для UI сообщением."""


@dataclass
class GoogleConfig:
    """Конфигурация OAuth-клиента Google."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=lambda: list(DEFAULT_SCOPES))
    authorization_endpoint: str = GOOGLE_AUTHORIZATION_ENDPOINT
    token_endpoint: str = GOOGLE_TOKEN_ENDPOINT
    userinfo_endpoint: str = GOOGLE_USERINFO_ENDPOINT


def load_config() -> GoogleConfig:
    """Читаем конфигурацию из ``st.secrets["google_oauth"]``."""
    try:
        import streamlit as st

        cfg = st.secrets["google_oauth"]
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(
            "Не настроен раздел [google_oauth] в secrets.toml."
        ) from exc

    scopes = cfg.get("scopes") if hasattr(cfg, "get") else None
    missing = [k for k in ("client_id", "client_secret", "redirect_uri") if not cfg.get(k)]
    if missing:
        raise OAuthError(
            "В [google_oauth] не хватает полей: " + ", ".join(missing)
        )

    return GoogleConfig(
        client_id=str(cfg["client_id"]),
        client_secret=str(cfg["client_secret"]),
        redirect_uri=str(cfg["redirect_uri"]),
        scopes=[str(s) for s in scopes] if scopes else list(DEFAULT_SCOPES),
    )


def _make_session(cfg: GoogleConfig) -> OAuth2Session:
    return OAuth2Session(
        cfg.client_id,
        cfg.client_secret,
        scope=" ".join(cfg.scopes),
        redirect_uri=cfg.redirect_uri,
    )


def _naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _store_state(state: str, provider: str = "google") -> None:
    """Сохраняем одноразовый state в БД и чистим протухшие."""
    init_db()
    now = _naive_utc()
    with session_scope() as s:
        s.query(OAuthState).filter(OAuthState.expires_at < now).delete()
        s.add(
            OAuthState(
                state=state,
                provider=provider,
                expires_at=now + _STATE_TTL,
            )
        )


def consume_state(state: str, provider: str = "google") -> bool:
    """Проверяем и удаляем state. True — если он валиден и не протух."""
    if not state:
        return False
    with session_scope() as s:
        row = (
            s.query(OAuthState)
            .filter_by(state=state, provider=provider)
            .one_or_none()
        )
        if row is None:
            return False
        valid = row.expires_at >= _naive_utc()
        s.delete(row)
        return valid


def build_authorization_url(provider: str = "google") -> str:
    """Формируем URL для редиректа на страницу согласия Google.

    ``access_type=offline`` и ``prompt=consent`` нужны, чтобы Google выдал
    refresh_token (иначе при повторном входе его может не быть).
    """
    cfg = load_config()
    session = _make_session(cfg)
    state = secrets.token_urlsafe(32)
    _store_state(state, provider)

    url, _ = session.create_authorization_url(
        cfg.authorization_endpoint,
        state=state,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return url


def _fetch_userinfo(access_token: str) -> dict:
    resp = requests.get(
        GOOGLE_USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise OAuthError(f"Google отклонил запрос профиля: {resp.text}") from exc
    return resp.json()


def _expires_at_from_token(token: dict) -> datetime | None:
    expires_at = token.get("expires_at")
    if expires_at is not None:
        return datetime.fromtimestamp(int(expires_at), tz=timezone.utc).replace(
            tzinfo=None
        )
    expires_in = token.get("expires_in")
    if expires_in is not None:
        return _naive_utc() + timedelta(seconds=int(expires_in))
    return None


def _persist_user_and_token(userinfo: dict, token: dict, provider: str) -> int:
    """Создаём/обновляем пользователя и сохраняем его токены (зашифрованно)."""
    init_db()
    subject = userinfo.get("sub")
    if not subject:
        raise OAuthError("Google не вернул идентификатор пользователя (sub).")

    with session_scope() as s:
        user = (
            s.query(User)
            .filter_by(provider=provider, subject=subject)
            .one_or_none()
        )
        if user is None:
            user = User(provider=provider, subject=subject)
            s.add(user)
        user.email = userinfo.get("email")
        user.name = userinfo.get("name")
        user.picture = userinfo.get("picture")
        s.flush()  # получить user.id

        tok = (
            s.query(OAuthToken)
            .filter_by(user_id=user.id, provider=provider)
            .one_or_none()
        )
        if tok is None:
            tok = OAuthToken(user_id=user.id, provider=provider)
            s.add(tok)

        tok.access_token = encrypt(token["access_token"])
        # refresh_token Google отдаёт не всегда — сохраняем только если пришёл.
        if token.get("refresh_token"):
            tok.refresh_token = encrypt(token["refresh_token"])
        tok.token_type = token.get("token_type")
        tok.scope = token.get("scope")
        tok.expires_at = _expires_at_from_token(token)
        s.flush()
        return user.id


def complete_login(code: str, state: str, provider: str = "google") -> dict:
    """Обмен кода на токены, чтение профиля и сохранение. Возвращает пользователя."""
    if not consume_state(state, provider):
        raise OAuthError("Проверка безопасности не пройдена (неверный state).")

    cfg = load_config()
    session = _make_session(cfg)
    try:
        token = session.fetch_token(cfg.token_endpoint, code=code)
    except Exception as exc:  # noqa: BLE001
        raise OAuthError(f"Не удалось обменять код на токен: {exc}") from exc

    userinfo = _fetch_userinfo(token["access_token"])
    user_id = _persist_user_and_token(userinfo, token, provider)

    return {
        "id": user_id,
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }


def get_valid_access_token(user_id: int, provider: str = "google") -> str | None:
    """Возвращаем действующий access token, при необходимости обновляя его."""
    init_db()
    with session_scope() as s:
        tok = (
            s.query(OAuthToken)
            .filter_by(user_id=user_id, provider=provider)
            .one_or_none()
        )
        if tok is None:
            return None

        access_token = decrypt(tok.access_token)
        expires_at = tok.expires_at
        # Обновляем заранее (за 2 минуты до истечения).
        if expires_at is not None and expires_at <= _naive_utc() + timedelta(minutes=2):
            refresh_token = decrypt(tok.refresh_token)
            if not refresh_token:
                return None
            cfg = load_config()
            client = OAuth2Session(cfg.client_id, cfg.client_secret)
            try:
                new_token = client.refresh_token(
                    cfg.token_endpoint, refresh_token=refresh_token
                )
            except Exception as exc:  # noqa: BLE001
                raise OAuthError(f"Не удалось обновить токен доступа: {exc}") from exc

            access_token = new_token["access_token"]
            tok.access_token = encrypt(access_token)
            tok.expires_at = _expires_at_from_token(new_token)
            s.flush()

        return access_token
