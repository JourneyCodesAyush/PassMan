import sqlite3

import pytest

from passman.database import execute, execute_transaction, fetchall, fetchone


class TestInitDb:
    def test_creates_users_table(self, test_db):
        row = fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert row is not None

    def test_creates_passwords_table(self, test_db):
        row = fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='passwords'"
        )
        assert row is not None

    def test_init_db_is_idempotent(self, test_db):
        from passman.schema import init_db

        # Should not raise or wipe data when called again.
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        init_db()
        row = fetchone("SELECT username FROM users WHERE username=?", ("alice",))
        assert row is not None


class TestExecuteFetch:
    def test_execute_and_fetchone(self, test_db):
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        row = fetchone("SELECT username FROM users WHERE username=?", ("alice",))
        assert row == ("alice",)

    def test_fetchone_no_match_returns_none(self, test_db):
        assert (
            fetchone("SELECT username FROM users WHERE username=?", ("nope",)) is None
        )

    def test_fetchall_returns_all_matches(self, test_db):
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("bob", "hash", "salt"),
        )
        rows = fetchall("SELECT username FROM users ORDER BY username")
        assert rows == [("alice",), ("bob",)]

    def test_fetchall_no_match_returns_empty_list(self, test_db):
        assert fetchall("SELECT username FROM users") == []


class TestExecuteTransaction:
    def test_returns_rowcount_of_last_statement(self, test_db):
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        rowcount = execute_transaction(
            [
                ("DELETE FROM passwords WHERE username=?", ("alice",)),
                ("DELETE FROM users WHERE username=?", ("alice",)),
            ]
        )
        assert rowcount == 1

    def test_all_statements_are_applied(self, test_db):
        execute_transaction(
            [
                (
                    "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
                    ("alice", "hash", "salt"),
                ),
                (
                    "INSERT INTO passwords (username, name, password, description) "
                    "VALUES (?, ?, ?, ?)",
                    ("alice", "gmail", "ciphertext", ""),
                ),
            ]
        )
        assert fetchone("SELECT username FROM users WHERE username=?", ("alice",))
        assert fetchone(
            "SELECT name FROM passwords WHERE username=? AND name=?",
            ("alice", "gmail"),
        )

    def test_failure_partway_rolls_back_everything(self, test_db):
        # First statement is valid; second is malformed SQL and will raise.
        # Neither statement should persist.
        with pytest.raises(sqlite3.OperationalError):
            execute_transaction(
                [
                    (
                        "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
                        ("alice", "hash", "salt"),
                    ),
                    ("NOT VALID SQL", ()),
                ]
            )
        assert (
            fetchone("SELECT username FROM users WHERE username=?", ("alice",)) is None
        )


class TestForeignKeyEnforcement:
    def test_insert_password_for_nonexistent_user_fails(self, test_db):
        with pytest.raises(sqlite3.IntegrityError):
            execute(
                "INSERT INTO passwords (username, name, password, description) "
                "VALUES (?, ?, ?, ?)",
                ("ghost", "gmail", "ciphertext", ""),
            )

    def test_deleting_user_with_existing_entries_directly_fails(self, test_db):
        # This is the direct FK test that's been deferred across sessions:
        # create a user, add a password entry, then try to delete the user
        # row directly (bypassing auth.delete_user's correct delete order)
        # and confirm sqlite raises rather than silently orphaning the row.
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        execute(
            "INSERT INTO passwords (username, name, password, description) "
            "VALUES (?, ?, ?, ?)",
            ("alice", "gmail", "ciphertext", ""),
        )
        with pytest.raises(
            sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"
        ):
            execute("DELETE FROM users WHERE username=?", ("alice",))

    def test_deleting_user_with_no_entries_succeeds(self, test_db):
        execute(
            "INSERT INTO users (username, password, salt) VALUES (?, ?, ?)",
            ("alice", "hash", "salt"),
        )
        # No passwords row references 'alice', so this direct delete is fine.
        execute("DELETE FROM users WHERE username=?", ("alice",))
        assert (
            fetchone("SELECT username FROM users WHERE username=?", ("alice",)) is None
        )
