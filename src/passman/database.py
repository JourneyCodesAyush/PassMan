import sqlite3
from typing import Any

from passman.utils import get_app_data_dir

__all__ = ["execute", "fetchone", "fetchall"]

DB_PATH: str = str(get_app_data_dir() / "vault.db")


def _get_connection() -> sqlite3.Connection:
    """Open a new connection to the vault database, with foreign key
    constraint enforcement enabled.

    Returns:
        A `sqlite3.Connection` pointed at `DB_PATH`. Callers are
        expected to use this via a `with` block so the connection
        is committed/rolled back and closed automatically.
    """
    connection: sqlite3.Connection = sqlite3.connect(database=DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def execute(query: str, params: tuple[str, ...] = ()) -> None:
    """Run a write query (INSERT/UPDATE/DELETE/CREATE TABLE) against the vault.

    Args:
        query: A parameterized SQL statement. Always use `?`
            placeholders rather than string-formatting values in,
            to avoid SQL injection.
        params: Values to bind to the query's placeholders, in order.
    """
    with _get_connection() as connection:
        _: sqlite3.Cursor = connection.execute(query, params)


def fetchone(query: str, params: tuple[str, ...] = ()) -> Any:
    """Run a SELECT query and return a single row.

    Args:
        query: A parameterized SQL SELECT statement.
        params: Values to bind to the query's placeholders, in order.

    Returns:
        The first matching row as a tuple, or `None` if no row matches.
    """
    with _get_connection() as connection:
        response: sqlite3.Cursor = connection.execute(query, params)
        return response.fetchone()


def fetchall(query: str, params: tuple[str, ...] = ()) -> list[Any]:
    """Run a SELECT query and return all matching rows.

    Args:
        query: A parameterized SQL SELECT statement.
        params: Values to bind to the query's placeholders, in order.

    Returns:
        A list of matching rows as tuples. Empty list if no rows match.
    """
    with _get_connection() as connection:
        response: sqlite3.Cursor = connection.execute(query, params)
        return response.fetchall()
