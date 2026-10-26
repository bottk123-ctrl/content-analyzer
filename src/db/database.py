"""Настройка подключения к БД и фабрика сессий.

URL подключения определяется в таком порядке:
1. Переменная окружения ``DATABASE_URL`` (локальная разработка, CI).
2. ``st.secrets["database"]["url"]`` (Streamlit Cloud / прод).
3. Локальный SQLite-файл (значение по умолчанию).

На Streamlit Community Cloud файловая система непостоянна, поэтому для
продакшена ожидается внешний Postgres (Neon/Supabase и т.п.).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

_DEFAULT_SQLITE_URL = "sqlite:///content_analyzer.db"


def _normalize(url: str) -> str:
    """Приводим префикс драйвера к тому, что понимает SQLAlchemy 2.0."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _read_database_url() -> str:
    """Определяем URL БД из окружения, секретов или дефолта."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return _normalize(env_url)

    try:
        import streamlit as st

        secret_url = st.secrets["database"]["url"]
        if secret_url:
            return _normalize(str(secret_url))
    except Exception:  # noqa: BLE001 - секретов может не быть вовсе
        pass

    return _DEFAULT_SQLITE_URL


def get_engine() -> Engine:
    """Лениво создаём единственный Engine на процесс."""
    global _engine
    if _engine is None:
        url = _read_database_url()
        connect_args = (
            {"check_same_thread": False} if url.startswith("sqlite") else {}
        )
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args=connect_args,
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Фабрика сессий, привязанная к Engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), expire_on_commit=False, future=True
        )
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Контекстный менеджер: commit при успехе, rollback при ошибке."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Создаём таблицы, если их ещё нет. Идемпотентно."""
    Base.metadata.create_all(get_engine())
