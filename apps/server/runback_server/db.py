"""Database engine and session factory."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from runback_server.config import get_settings


def _make_engine():
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{settings.db_path.absolute()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = _make_engine()


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def create_all() -> None:
    """Create tables from SQLModel metadata. Tests use this; production uses Alembic."""
    SQLModel.metadata.create_all(engine)
