import base64
import hashlib

import argon2.exceptions
from argon2 import PasswordHasher
from cryptography.fernet import Fernet

__all__ = ["hash_password", "verify_password", "derive_key", "encrypt", "decrypt"]


def hash_password(password: str) -> str:
    """Hash a master password using Argon2.

    Used at signup to produce a value safe to store in place of the
    plaintext master password. Argon2 includes its own random salt
    internally, so no separate salt needs to be passed in.

    Args:
        password: The plaintext master password.

    Returns:
        An Argon2 hash string, safe to store in the database.
    """
    ph: PasswordHasher = PasswordHasher()
    hashed: str = ph.hash(password=password)
    return hashed


def verify_password(stored_hash: str, attempted: str) -> bool:
    """Check a login attempt against a stored Argon2 hash.

    Args:
        stored_hash: The Argon2 hash previously produced by
            `hash_password` and stored at signup.
        attempted: The plaintext password entered at login.

    Returns:
        `True` if `attempted` matches `stored_hash`.
        `False` if the password is simply wrong.

    Raises:
        argon2.exceptions.InvalidHashError: If `stored_hash` is
            malformed — indicates data corruption, not user error.
        argon2.exceptions.VerificationError: If verification fails
            for some other reason.
    """
    ph: PasswordHasher = PasswordHasher()
    try:
        return ph.verify(stored_hash, attempted)
    except argon2.exceptions.VerifyMismatchError:
        return False


def derive_key(salt: str, master_password: str) -> bytes:
    """Derive a Fernet-compatible encryption key from the master password.

    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations, then base64
    url-safe encodes the result so it can be used directly as a
    Fernet key. This key is never stored — it's re-derived at login
    each time and kept in memory only for the duration of the session.

    Args:
        salt: The user's unique salt, generated at signup with
            `secrets.token_hex(32)` and stored alongside their
            Argon2 hash.
        master_password: The plaintext master password.

    Returns:
        A base64 url-safe encoded key suitable for `Fernet(key=...)`.
    """
    key: bytes = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=master_password.encode(),
        salt=salt.encode(),
        iterations=600000,
    )
    return base64.urlsafe_b64encode(key)


def encrypt(key: bytes, plaintext: str) -> str:
    """Encrypt a plaintext string using Fernet (AES-128-CBC + HMAC-SHA256).

    Args:
        key: A Fernet-compatible key, as returned by `derive_key`.
        plaintext: The value to encrypt (e.g. a vault password).

    Returns:
        The encrypted value as a string, safe to store in the database.
    """
    fernet: Fernet = Fernet(key=key)
    encrypted: bytes = fernet.encrypt(data=plaintext.encode())
    return encrypted.decode()


def decrypt(key: bytes, cipher: str) -> str:
    """Decrypt a Fernet-encrypted string back to plaintext.

    Args:
        key: The same Fernet-compatible key used to encrypt `cipher`.
            A key derived from the wrong master password will fail
            to decrypt (raises `cryptography.fernet.InvalidToken`).
        cipher: The encrypted string, as returned by `encrypt`.

    Returns:
        The original plaintext string.
    """
    fernet: Fernet = Fernet(key=key)
    decrypted: bytes = fernet.decrypt(token=cipher)
    return decrypted.decode()
