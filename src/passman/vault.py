from typing import Any

from passman.crypto import encrypt, decrypt
from passman.database import execute, fetchone

__all__ = ["create", "read", "update", "delete"]


def create(
    username: str,
    name: str,
    plaintext_password: str,
    key: bytes,
    description: str | None = None,
) -> None:
    query: str = (
        """INSERT INTO passwords (username, name, password, description) VALUES (?, ?, ?, ?)"""
    )

    encrypted_password: str = encrypt(key=key, plaintext=plaintext_password)
    params: tuple[str, ...] = (username, name, encrypted_password, description or "")
    execute(query=query, params=params)


def read(username: str, name: str, key: bytes) -> tuple[str, str] | None:
    query: str = (
        """SELECT username, name, password, description FROM passwords WHERE username=? AND name=?"""
    )
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
    encrypted_password: str = encrypt(key=key, plaintext=new_password)
    query: str = (
        """UPDATE passwords SET password=?, description=? WHERE username=? AND name=?"""
    )

    if description is None:
        existing = read(username=username, name=name, key=key)
        description = existing[1] if existing else ""

    params: tuple[str, ...] = (encrypted_password, description, username, name)
    execute(query=query, params=params)


def delete(username: str, name: str) -> None:
    query: str = """DELETE FROM passwords WHERE username=? AND name=?"""
    params: tuple[str, ...] = (username, name)
    execute(query=query, params=params)
