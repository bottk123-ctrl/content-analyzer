"""Симметричное шифрование OAuth-токенов перед записью в БД.

Используется Fernet (AES-128-CBC + HMAC). Ключ берётся из
``security.token_encryption_key`` в secrets.toml либо из переменной
окружения ``TOKEN_ENCRYPTION_KEY``.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

_cached_fernet: Fernet | None = None


def generate_key() -> str:
    """Сгенерировать новый ключ Fernet (для первичной настройки)."""
    return Fernet.generate_key().decode()


def _read_key() -> str:
    env_key = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if env_key:
        return env_key

    try:
        import streamlit as st

        secret_key = st.secrets["security"]["token_encryption_key"]
        if secret_key:
            return str(secret_key)
    except Exception:  # noqa: BLE001
        pass

    raise RuntimeError(
        "Не задан ключ шифрования токенов. Установите "
        "security.token_encryption_key в secrets.toml либо переменную "
        "окружения TOKEN_ENCRYPTION_KEY."
    )


def _get_fernet() -> Fernet:
    global _cached_fernet
    if _cached_fernet is None:
        _cached_fernet = Fernet(_read_key().encode())
    return _cached_fernet


def encrypt(value: str | None) -> str | None:
    """Зашифровать строку (None пропускаем как есть)."""
    if value is None:
        return None
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    """Расшифровать строку (None пропускаем как есть)."""
    if value is None:
        return None
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError(
            "Не удалось расшифровать токен: неверный ключ шифрования."
        ) from exc
