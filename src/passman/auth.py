import secrets

from passman.database import execute, fetchone
from passman.crypto import verify_password, hash_password

__all__ = ["signup", "login"]


def signup(username: str, password: str) -> str:
    """Create a new user with a hashed master password and unique salt.

    Args:
        username: The desired username. Must be unique — inserting a
            duplicate will raise `sqlite3.IntegrityError` since
            `username` is the table's primary key.
        password: The plaintext master password to hash and store.

    Returns:
        The newly generated salt, for immediate use in deriving the
        session's encryption key via `crypto.derive_key`.
    """
    salt: str = secrets.token_hex(32)

    query: str = """INSERT INTO users (username, password, salt) VALUES (?, ?, ?)"""

    hashed: str = hash_password(password=password)
    params: tuple[str, ...] = (username, hashed, salt)

    execute(query=query, params=params)
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
