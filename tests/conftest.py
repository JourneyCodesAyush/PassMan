import pytest

import passman.database as database
from passman.schema import init_db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Point the app at a throwaway sqlite file for the duration of a test.

    `database.DB_PATH` is a module-level constant, but `_get_connection()`
    reads it fresh from the module namespace on every call -- so patching
    the attribute here is sufficient to redirect every `execute`/`fetchone`/
    `fetchall`/`execute_transaction` call without touching any real user
    data. `init_db()` then creates the `users`/`passwords` tables in the
    fresh file.
    """
    db_path = tmp_path / "test_vault.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    init_db()
    return db_path
