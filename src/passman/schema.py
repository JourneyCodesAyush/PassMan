from passman.database import execute

__all__ = ["init_db"]


def init_db() -> None:
    _create_users_table()
    _create_users_password_table()


def _create_users_table() -> None:
    query: str = """CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    salt TEXT NOT NULL
    )"""
    execute(query=query)


def _create_users_password_table() -> None:
    query: str = """CREATE TABLE IF NOT EXISTS passwords (
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    PRIMARY KEY (username, name)
    )"""
    execute(query=query)
