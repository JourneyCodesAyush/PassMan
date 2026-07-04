from passman.database import execute

__all__ = ["init_db"]


def init_db() -> None:
    """Initialize the database, creating all required tables if they
    don't already exist.

    Safe to call on every startup — table creation uses
    `CREATE TABLE IF NOT EXISTS`, so existing data is left untouched.
    """
    _create_users_table()
    _create_users_password_table()


def _create_users_table() -> None:
    """Create the `users` table if it doesn't already exist.

    Schema:
        username TEXT PRIMARY KEY — unique login name
        password TEXT NOT NULL    — Argon2 hash of the master password
        salt TEXT NOT NULL        — PBKDF2 salt, generated at signup
    """
    query: str = """CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    salt TEXT NOT NULL
    )"""
    execute(query=query)


def _create_users_password_table() -> None:
    """Create the `passwords` table if it doesn't already exist.

    Schema:
        username TEXT NOT NULL    — owner of the entry, references users.username
        name TEXT NOT NULL        — label for the entry (e.g. "gmail")
        password TEXT NOT NULL    — Fernet-encrypted password
        description TEXT          — optional free-text note
        PRIMARY KEY (username, name)
        FOREIGN KEY (username) REFERENCES users(username)
    """
    query: str = """CREATE TABLE IF NOT EXISTS passwords (
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    description TEXT,
    PRIMARY KEY (username, name),
    FOREIGN KEY (username) REFERENCES users(username)
    )"""
    execute(query=query)
