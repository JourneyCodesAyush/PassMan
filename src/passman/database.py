import sqlite3
from typing import Any

from passman.utils import get_app_data_dir

__all__ = ["execute", "fetchone", "fetchall"]

DB_PATH: str = str(get_app_data_dir() / "vault.db")


def _get_connection() -> sqlite3.Connection:
    connection: sqlite3.Connection = sqlite3.connect(database=DB_PATH)
    return connection


def execute(query: str, params: tuple[str, ...] = ()) -> None:
    with _get_connection() as connection:
        _: sqlite3.Cursor = connection.execute(query, params)


def fetchone(query: str, params: tuple[str, ...] = ()) -> Any:
    with _get_connection() as connection:
        response: sqlite3.Cursor = connection.execute(query, params)
        return response.fetchone()


def fetchall(query: str, params: tuple[str, ...] = ()) -> list[Any]:
    with _get_connection() as connection:
        response: sqlite3.Cursor = connection.execute(query, params)
        return response.fetchall()
