# PassMan

![Python Version](https://img.shields.io/badge/python-3.14+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**passman** is a local-first CLI password manager that keeps your passwords encrypted and on your machine.

> Argon2 hashing, Fernet encryption, PBKDF2 key derivation — no cloud, no network, no trust required.

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
```

Once logged in, you get an interactive REPL shell:

```txt
Commands:
  (a)dd <name>     — add a password (prompted securely)
  (g)et <name>     — retrieve a password
  (u)pdate <name>  — update a password (prompted securely)
  (d)elete <name>  — delete a password
  (e)xit / (b)ye   — exit the shell
```

---

## Security Design

- **Master password** — hashed with Argon2, never stored in plaintext
- **Vault passwords** — encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- **Key derivation** — PBKDF2-HMAC-SHA256 with 600,000 iterations, unique salt per user
- **Salt** — generated at signup with `secrets.token_hex(32)`, stored in the database
- **Session key** — derived at login, lives in memory only, never persisted
- **SQL injection** — parameterized queries throughout

---

## Motivation

I read about Bitwarden, then KeePassX, and thought — how hard could it be to build one myself? Turns out, not that hard if you let the stdlib do the heavy lifting and let `argon2-cffi` and `cryptography` handle the hard parts.

`passman` has two runtime dependencies. Everything else is stdlib.

---

## License

This project is licensed under the [**MIT License**](./LICENSE).
