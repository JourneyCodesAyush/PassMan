from typing import Any

from passman.crypto import encrypt, decrypt
from passman.database import execute, fetchone


def create(username: str, name: str, plaintext_password: str, key: bytes) -> None:
    query: str = """INSERT INTO passwords (username, name, password) VALUES (?, ?, ?)"""
    encrypted_password: str = encrypt(key=key, plaintext=plaintext_password)
    params: tuple[str, ...] = (username, name, encrypted_password)
    execute(query=query, params=params)


def read(username: str, name: str, key: bytes) -> str | None:
    query: str = (
        """SELECT username, name, password FROM passwords WHERE username=? AND name=?"""
    )
    params: tuple[str, ...] = (username, name)
    result: Any = fetchone(query=query, params=params)
    if result is None:
        return None
    decrypted_password: str = decrypt(key=key, cipher=result[2])
    return decrypted_password


def update(username: str, name: str, new_password: str, key: bytes) -> None:
    encrypted_password: str = encrypt(key=key, plaintext=new_password)
    query: str = """UPDATE passwords SET password=? WHERE username=? AND name=?"""
    params: tuple[str, ...] = (encrypted_password, username, name)
    execute(query=query, params=params)


def delete(username: str, name: str) -> None:
    query: str = """DELETE FROM passwords WHERE username=? AND name=?"""
    params: tuple[str, ...] = (username, name)
    execute(query=query, params=params)
