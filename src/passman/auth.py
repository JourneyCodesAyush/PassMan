import secrets

from passman.database import execute, fetchone
from passman.crypto import verify_password, hash_password

__all__ = ["signup", "login"]


def signup(username: str, password: str) -> str:
    salt: str = secrets.token_hex(32)

    query: str = """INSERT INTO users (username, password, salt) VALUES (?, ?, ?)"""

    hashed: str = hash_password(password=password)
    params: tuple[str, ...] = (username, hashed, salt)

    execute(query=query, params=params)
    return salt


def login(username: str, password: str) -> str | None:
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
