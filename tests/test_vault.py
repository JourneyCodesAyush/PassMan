import pytest

from passman.auth import signup
from passman.crypto import derive_key
from passman import vault


@pytest.fixture
def alice(test_db):
    """Create a real user (required by the FK on passwords.username) and
    derive their session key, the same way __main__.py does after login.
    """
    salt = signup(username="alice", password="hunter2")
    key = derive_key(salt=salt, master_password="hunter2")
    return {"username": "alice", "key": key}


class TestCreateAndRead:
    def test_create_then_read_roundtrip(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="my-secret",
            key=alice["key"],
            description="personal email",
        )
        result = vault.read(
            username=alice.get("username"), name="gmail", key=alice.get("key")
        )
        assert result is not None
        password, description = result
        assert password == "my-secret"
        assert description == "personal email"

    def test_create_without_description_stores_empty_string(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="my-secret",
            key=alice["key"],
        )
        result = vault.read(username=alice["username"], name="gmail", key=alice["key"])
        assert result is not None
        _, description = result
        assert description == ""

    def test_read_nonexistent_entry_returns_none(self, alice):
        assert (
            vault.read(username=alice["username"], name="nope", key=alice["key"])
            is None
        )

    def test_create_for_nonexistent_user_raises_integrity_error(self, test_db):
        import sqlite3

        key = derive_key(salt="somesalt", master_password="hunter2")
        with pytest.raises(sqlite3.IntegrityError):
            vault.create(
                username="ghost",
                name="gmail",
                plaintext_password="my-secret",
                key=key,
            )


class TestUpdate:
    def test_update_changes_password(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="old-secret",
            key=alice["key"],
            description="personal email",
        )
        vault.update(
            username=alice["username"],
            name="gmail",
            new_password="new-secret",
            key=alice["key"],
            description="personal email",
        )
        result = vault.read(username=alice["username"], name="gmail", key=alice["key"])

        assert result is not None
        password, _ = result
        assert password == "new-secret"

    def test_update_without_description_preserves_existing(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="old-secret",
            key=alice["key"],
            description="personal email",
        )
        vault.update(
            username=alice["username"],
            name="gmail",
            new_password="new-secret",
            key=alice["key"],
            description=None,
        )
        result = vault.read(username=alice["username"], name="gmail", key=alice["key"])

        assert result is not None
        password, description = result
        assert password == "new-secret"
        assert description == "personal email"

    def test_update_with_new_description_overwrites(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="old-secret",
            key=alice["key"],
            description="personal email",
        )
        vault.update(
            username=alice["username"],
            name="gmail",
            new_password="new-secret",
            key=alice["key"],
            description="work email now",
        )
        result = vault.read(username=alice["username"], name="gmail", key=alice["key"])

        assert result is not None
        _, description = result
        assert description == "work email now"

    def test_update_nonexistent_entry_is_a_silent_noop(self, alice):
        # vault.update has no existence check -- an UPDATE matching zero
        # rows simply affects nothing. Documenting that behavior here so
        # a future change to add validation doesn't happen unnoticed.
        vault.update(
            username=alice["username"],
            name="nope",
            new_password="new-secret",
            key=alice["key"],
            description="whatever",
        )
        assert (
            vault.read(username=alice["username"], name="nope", key=alice["key"])
            is None
        )


class TestDelete:
    def test_delete_removes_entry(self, alice):
        vault.create(
            username=alice["username"],
            name="gmail",
            plaintext_password="my-secret",
            key=alice["key"],
        )
        vault.delete(username=alice["username"], name="gmail")
        assert (
            vault.read(username=alice["username"], name="gmail", key=alice["key"])
            is None
        )

    def test_delete_nonexistent_entry_does_not_raise(self, alice):
        vault.delete(username=alice["username"], name="nope")
