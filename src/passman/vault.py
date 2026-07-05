from typing import Any

from passman.crypto import decrypt, encrypt
from passman.database import execute, fetchone

__all__ = ["create", "read", "update", "delete"]


def create(
    username: str,
    name: str,
    plaintext_password: str,
    key: bytes,
    description: str | None = None,
) -> None:
    """Encrypt and store a new password entry for a user.

    Args:
        username: Owner of the entry.
        name: Unique label for the entry (e.g. "gmail").
        plaintext_password: The password to encrypt and store.
        key: Fernet key derived from the user's master password.
        description: Optional free-text note. Stored as an empty
            string if not provided.
    """
    query: str = """INSERT INTO passwords (username, name, password, description) VALUES (?, ?, ?, ?)"""

    encrypted_password: str = encrypt(key=key, plaintext=plaintext_password)
    params: tuple[str, ...] = (username, name, encrypted_password, description or "")
    execute(query=query, params=params)


def read(username: str, name: str, key: bytes) -> tuple[str, str] | None:
    """Retrieve and decrypt a single password entry.

    Args:
        username: Owner of the entry.
        name: Label of the entry to look up.
        key: Fernet key derived from the user's master password.

    Returns:
        A `(decrypted_password, description)` tuple, or `None` if
        no entry matches `username` and `name`.
    """
    query: str = """SELECT username, name, password, description FROM passwords WHERE username=? AND name=?"""
    params: tuple[str, ...] = (username, name)
    result: Any = fetchone(query=query, params=params)
    if result is None:
        return None
    decrypted_password: str = decrypt(key=key, cipher=result[2])
    return (decrypted_password, result[3])


def update(
    username: str,
    name: str,
    new_password: str,
    key: bytes,
    description: str | None = None,
) -> None:
    """Re-encrypt and overwrite an existing password entry.

    If `description` is omitted, the entry's current description is
    preserved by querying it directly, without decrypting the
    existing password.

    Args:
        username: Owner of the entry.
        name: Label of the entry to update.
        new_password: The new plaintext password to encrypt and store.
        key: Fernet key derived from the user's master password.
        description: Optional new description. Pass `None` to leave
            the existing description unchanged.
    """
    encrypted_password: str = encrypt(key=key, plaintext=new_password)
    query: str = (
        """UPDATE passwords SET password=?, description=? WHERE username=? AND name=?"""
    )

    if description is None:
        lookup_query: str = """SELECT username, name, description FROM passwords WHERE username=? AND name=?"""
        lookup_params: tuple[str, ...] = (username, name)
        existing = fetchone(query=lookup_query, params=lookup_params)
        description = existing[2] if existing else ""

    assert isinstance(description, str)
    params: tuple[str, ...] = (encrypted_password, description, username, name)
    execute(query=query, params=params)


def delete(username: str, name: str) -> None:
    """Permanently remove a password entry.

    Args:
        username: Owner of the entry.
        name: Label of the entry to delete.
    """
    query: str = """DELETE FROM passwords WHERE username=? AND name=?"""
    params: tuple[str, ...] = (username, name)
    execute(query=query, params=params)
