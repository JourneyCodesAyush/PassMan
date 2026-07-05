# PassMan

![Python Version](https://img.shields.io/badge/python-3.14+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Latest Release](https://img.shields.io/github/v/tag/JourneyCodesAyush/passman?label=version)

**passman** is a local-first CLI password manager that keeps your passwords encrypted and on your machine.

> Argon2 hashing, Fernet encryption, PBKDF2 key derivation — no cloud, no network, no trust required.

![demo](assets/demo.png)

---

## Quick Start

```powershell
git clone https://github.com/JourneyCodesAyush/passman.git
cd passman
uv sync
uv pip install -e . --link-mode=copy
passman signup
```

---

## Usage

```bash
# Create a new user
passman signup

# Login as an existing user
passman -u <username>

# Permanently delete a user and all of their saved entries
passman -d <username>

# List all saved entry names without logging in
passman list

# Show the installed version
passman -v
```

> [!NOTE]
> `-u`, `-d`, and the `signup`/`list` subcommands are mutually exclusive — you can only use one per invocation.

Once logged in, you get an interactive REPL shell:

```txt
Commands:
  (a)dd <name>                — add a password (prompted securely)
  (g)et <name>                — retrieve a password
  (u)pdate <name>             — update a password (prompted securely)
  (d)elete <name>             — delete a password
  (l)ist                      — list all saved entry names
  gen <name> [description]    — generate and save a random password
  export [path]               — export vault to a JSON file
  import <path>                — import entries from a JSON file
  (e)xit / (b)ye              — exit the shell
```

Run `help <command>` inside the REPL for details on any command.

### `gen` options

```txt
gen <name> [description] [-l LENGTH] [-S] [-D]

  -l, --length LENGTH   password length (default: 16, minimum: 8)
  -S, --no-symbols      exclude symbols
  -D, --no-digits       exclude digits
```

If an entry with the same name already exists, you'll be prompted to overwrite it before the new password is generated.

---

## Security Design

- **Master password** — hashed with Argon2, never stored in plaintext
- **Vault passwords** — encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- **Key derivation** — PBKDF2-HMAC-SHA256 with 600,000 iterations, unique salt per user
- **Salt** — generated at signup with `secrets.token_hex(32)`, stored in the database
- **Session key** — derived at login, lives in memory only, never persisted
- **SQL injection** — parameterized queries throughout

---

## Data Storage

PassMan stores all data locally in a SQLite database. No data ever leaves your machine.

| Platform  | Location                                                                 |
| --------- | ------------------------------------------------------------------------ |
| Windows   | `%LOCALAPPDATA%\.passman\vault.db`                                       |
| macOS     | `~/Library/Application Support/.passman/vault.db`                        |
| Linux/BSD | `$XDG_DATA_HOME/.passman/vault.db` or `~/.local/share/.passman/vault.db` |

> **Note:** Python bundles SQLite in its standard library — no separate SQLite installation is needed.

> [!WARNING]
> **There is no password recovery.** Your vault key is derived from your master password and never stored anywhere. If you forget your master password, your encrypted vault is permanently inaccessible. Back up your master password somewhere safe.

> [!NOTE]
> **Upgrading from before v0.4.0?** The `description` field was added to the `passwords` table in v0.4.0. Existing vaults need a one-time manual migration:
>
> ```sql
> ALTER TABLE passwords ADD COLUMN description TEXT;
> ```

> [!NOTE]
> **Upgrading from before v0.7.0?** A `FOREIGN KEY` constraint linking `passwords.username` to `users.username` was added in v0.7.0. This is not applied retroactively to existing vaults, so orphaned entries from before this version (if any) are not automatically cleaned up or blocked.

---

## Export / Import

Entries can be exported to a plaintext JSON file for backup or migration, and re-imported later:

```json
[
  {
    "name": "gmail",
    "password": "decrypted_plaintext",
    "description": "personal email"
  }
]
```

`description` is optional on import. If an imported name already exists in your vault, you'll be prompted per-conflict to skip or overwrite it.

> [!WARNING]
> Exported files contain **decrypted plaintext passwords**. Store and delete them carefully.

---

## Running Tests

PassMan uses `pytest` for its test suite, covering `crypto`, `generator`, `schema`, `database`, `auth`, and `vault`.

```bash
uv run pytest
```

Add `-v` for verbose output. Tests run against a throwaway temporary database for each test — your real vault at `~/.local/share/.passman/vault.db` (or the platform equivalent) is never touched.

---

## Contributing

Contributions are welcome. Please follow these guidelines:

- Fork the repository and create a branch: `fix/bug-name` or `test/area-name`
- Follow the commit style: `type(scope): message`, describing the behavior or intent of the change rather than the diff itself
- Run `uv run pytest -v` and `uv run ruff check .` / `uv run ruff format .` before submitting a pull request
- Open a pull request with a clear description of your changes

CI runs lint and tests automatically on every push and PR against `main` — a PR won't be mergeable until both pass.

### Commit Types

| Type  | Description                      |
| ----- | -------------------------------- |
| feat  | New features                     |
| fix   | Bug fixes                        |
| test  | Adding or updating tests         |
| docs  | Documentation changes            |
| chore | Maintenance, deps, version bumps |
| ci    | CI/CD changes                    |

### Commit Scopes

| Scope     | Description                         |
| --------- | ----------------------------------- |
| auth      | Changes to signup/login/delete_user |
| vault     | Changes to password entry CRUD      |
| crypto    | Changes to hashing/encryption/keys  |
| generator | Changes to password generation      |
| schema    | Changes to table definitions        |
| db        | Changes to database helpers         |
| cli       | Changes to the CLI entry point      |
| conftest  | Changes to shared test fixtures     |
| pyproject | Changes to project/build config     |

Omit the scope only when a commit bundles multiple unrelated files (e.g. release/version-bump commits).

---

## Motivation

I read about Bitwarden, then KeePassX, and thought — how hard could it be to build one myself? Turns out, not that hard if you let the stdlib do the heavy lifting and let `argon2-cffi` and `cryptography` handle the hard parts.

`passman` depends on `argon2-cffi`, `cryptography`, and `jsonschema` for hashing, encryption, and import validation, respectively. Everything else is stdlib.

---

## License

This project is licensed under the [**MIT License**](./LICENSE).
