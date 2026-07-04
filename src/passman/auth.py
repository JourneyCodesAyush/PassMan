import sqlite3
import secrets

from passman.database import execute, fetchone, execute_transaction
from passman.crypto import verify_password, hash_password

__all__ = ["signup", "login", "delete_user"]


def signup(username: str, password: str) -> str:
    """Create a new user with a hashed master password and unique salt.

    Args:
        username: The desired username. Must be unique.
        password: The plaintext master password to hash and store.

    Returns:
        The newly generated salt, for immediate use in deriving the
        session's encryption key via `crypto.derive_key`.

    Raises:
        ValueError: If `username` is already taken.
    """
    salt: str = secrets.token_hex(32)

    query: str = """INSERT INTO users (username, password, salt) VALUES (?, ?, ?)"""

    hashed: str = hash_password(password=password)
    params: tuple[str, ...] = (username, hashed, salt)

    try:
        execute(query=query, params=params)
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' is already taken") from None

    return salt


def login(username: str, password: str) -> str | None:
    """Verify a login attempt against the stored Argon2 hash.

    Args:
        username: The username attempting to log in.
        password: The plaintext master password entered.

    Returns:
        The user's stored salt if the username exists and the
        password is correct, so the caller can derive the session's
        encryption key. Returns `None` if the username doesn't exist
        or the password is wrong — the two cases are indistinguishable
        by design, to avoid leaking which one failed.
    """
    query: str = """SELECT username, password, salt FROM users WHERE username=?"""
    params: tuple[str, ...] = (username,)
    result = fetchone(query=query, params=params)
    if result is None:
        return None
    else:
        login_successful: bool = verify_password(
            stored_hash=result[1], attempted=password
        )
        if login_successful:
            return result[2]
        else:
            return None


def delete_user(username: str) -> bool:
    """Permanently delete a user and all of their saved password entries.

    Deletes `passwords` rows before the `users` row, in a single
    transaction -- required because passwords.username carries a
    FOREIGN KEY back to users.username with enforcement on; the reverse
    order would raise FOREIGN KEY constraint failed for any user with
    existing entries. Since both statements run in one transaction, a
    failure partway through rolls back rather than leaving a
    passwordless orphaned account.

    Note: this function performs no password verification itself --
    callers are expected to confirm the caller's identity (e.g. via
    `login`) before invoking this.

    Args:
        username: The username of the account to delete.

    Returns:
        True if a user row was deleted, False if no matching user existed.
    """
    query1: str = """DELETE FROM passwords WHERE username=?"""
    params1: tuple[str, ...] = (username,)

    query2: str = """DELETE FROM users WHERE username=?"""
    params2: tuple[str, ...] = (username,)

    rows_affected = execute_transaction(
        statements=[(query1, params1), (query2, params2)]
    )

    return rows_affected > 0
