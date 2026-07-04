# Changelog

All notable changes to PassMan are documented in this file.

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) guidelines and uses [Semantic Versioning](https://semver.org/).

---

## 0.7.1

### Fixed

- `vault.update()` no longer fails when called without an explicit `description` — a shadowed query variable caused the description-lookup SELECT to run with the UPDATE statement's parameter count, raising `sqlite3.ProgrammingError` on any update that omitted a description for an existing entry.

---

## v0.7.0

### Added

- `-d/--delete` flag to permanently delete a user and all of their saved password entries
- `FOREIGN KEY` constraint on `passwords.username` referencing `users.username`, with per-connection enforcement (`PRAGMA foreign_keys = ON`)
- `execute_transaction` helper for atomic multi-statement writes

### Fixed

- Combining `-u`/`--user` with a subcommand (`signup`/`list`) no longer silently picks one — now errors clearly
- Exception handling in `main()` now works for the installed binary, not just direct/module invocation
- Duplicate username on signup now raises a clear `ValueError` instead of leaking a raw SQL error
- `verify_password` no longer silently swallows all exceptions — only catches the expected wrong-password case, letting corrupted-hash errors propagate

### Changed

- `vault.update()` now fetches the existing `description` directly via a separate query instead of decrypting the full entry through `read()`

---

## v0.6.0

### Added

- `gen` command: generates passwords using `secrets`-based randomness, with configurable length and symbol/digit inclusion, and saves them directly to the vault
- Overwrite confirmation prompt when `gen` targets an existing entry

### Changed

- Overwrite path on entry conflicts now uses a single `update()` call instead of `delete()` + `create()`

---

## v0.5.0

### Added

- `export` command to export a user's saved passwords as JSON
- `import` command to import passwords from a JSON file, with schema validation (`jsonschema`)
- Conflict prompt when importing an entry that already exists

### Changed

- Command documentation moved into docstrings; manual help output removed in favor of `cmd`'s built-in help generation

---

## v0.4.0

### Added

- `description` column on the `passwords` table
- Optional description support across vault CRUD operations and CLI output

---

## v0.3.0

### Added

- In-REPL `list`/`l` command to display all saved password entry names for the logged-in user

---

## v0.2.0

### Added

- `-v`/`--version` flag
- Top-level `list` subcommand to display all registered usernames

---

## v0.1.0

Initial release.

### Added

- Argon2-based password hashing and verification (`crypto.py`)
- Fernet-based encryption/decryption for stored passwords
- SQLite-backed storage with query execution and fetch helpers (`database.py`)
- Cross-platform app data directory resolution (Windows, macOS, Linux)
- User signup and login (`auth.py`)
- Vault CRUD operations for password entries (`vault.py`)
- Interactive REPL shell (`cmd`-based) with argparse entry point
- Input validation for empty required fields
- ASCII art banner and startup intro message
- `__all__` exports restricting each module's public API
- PyInstaller build script for standalone executables
