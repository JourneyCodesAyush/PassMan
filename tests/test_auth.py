import pytest

from passman.auth import delete_user, login, signup
from passman.database import execute, fetchone


class TestSignup:
    def test_signup_creates_user(self, test_db):
        signup(username="alice", password="hunter2")
        row = fetchone("SELECT username FROM users WHERE username=?", ("alice",))
        assert row is not None

    def test_signup_returns_a_salt(self, test_db):
        salt = signup(username="alice", password="hunter2")
        assert isinstance(salt, str)
        assert len(salt) == 64  # secrets.token_hex(32) -> 64 hex chars

    def test_signup_stores_hash_not_plaintext(self, test_db):
        signup(username="alice", password="hunter2")
        row = fetchone("SELECT password FROM users WHERE username=?", ("alice",))
        assert row[0] != "hunter2"

    def test_signup_duplicate_username_raises(self, test_db):
        signup(username="alice", password="hunter2")
        with pytest.raises(ValueError, match="already taken"):
            signup(username="alice", password="different")


class TestLogin:
    def test_login_correct_credentials_returns_salt(self, test_db):
        salt = signup(username="alice", password="hunter2")
        result = login(username="alice", password="hunter2")
        assert result == salt

    def test_login_wrong_password_returns_none(self, test_db):
        signup(username="alice", password="hunter2")
        assert login(username="alice", password="wrong") is None

    def test_login_nonexistent_user_returns_none(self, test_db):
        assert login(username="ghost", password="hunter2") is None


class TestDeleteUser:
    def test_delete_user_removes_user_row(self, test_db):
        signup(username="alice", password="hunter2")
        assert delete_user(username="alice") is True
        assert (
            fetchone("SELECT username FROM users WHERE username=?", ("alice",)) is None
        )

    def test_delete_user_removes_password_entries(self, test_db):
        signup(username="alice", password="hunter2")
        execute(
            "INSERT INTO passwords (username, name, password, description) "
            "VALUES (?, ?, ?, ?)",
            ("alice", "gmail", "ciphertext", ""),
        )
        delete_user(username="alice")
        row = fetchone(
            "SELECT name FROM passwords WHERE username=? AND name=?",
            ("alice", "gmail"),
        )
        assert row is None

    def test_delete_user_with_multiple_entries_does_not_raise_fk_error(self, test_db):
        # This is the case that requires deleting passwords before users:
        # a naive reverse-order delete would raise FOREIGN KEY constraint
        # failed here.
        signup(username="alice", password="hunter2")
        for name in ("gmail", "github", "bank"):
            execute(
                "INSERT INTO passwords (username, name, password, description) "
                "VALUES (?, ?, ?, ?)",
                ("alice", name, "ciphertext", ""),
            )
        assert delete_user(username="alice") is True

    def test_delete_nonexistent_user_returns_false(self, test_db):
        assert delete_user(username="ghost") is False

    def test_delete_user_does_not_affect_other_users(self, test_db):
        signup(username="alice", password="hunter2")
        signup(username="bob", password="hunter3")
        delete_user(username="alice")
        assert (
            fetchone("SELECT username FROM users WHERE username=?", ("bob",))
            is not None
        )
