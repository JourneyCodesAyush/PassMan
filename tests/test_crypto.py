import base64

import argon2.exceptions
import pytest
from cryptography.fernet import InvalidToken

from passman.crypto import decrypt, derive_key, encrypt, hash_password, verify_password


class TestHashAndVerifyPassword:
    def test_hash_password_returns_string(self):
        assert isinstance(hash_password("correct horse battery staple"), str)

    def test_hash_password_is_nondeterministic(self):
        # Argon2 embeds its own random salt, so hashing the same password
        # twice must produce two different strings.
        first = hash_password("hunter2")
        second = hash_password("hunter2")
        assert first != second

    def test_verify_password_correct(self):
        hashed = hash_password("hunter2")
        assert verify_password(stored_hash=hashed, attempted="hunter2") is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("hunter2")
        assert verify_password(stored_hash=hashed, attempted="wrong") is False

    def test_verify_password_malformed_hash_raises(self):
        with pytest.raises(argon2.exceptions.InvalidHashError):
            verify_password(stored_hash="not-a-real-argon2-hash", attempted="hunter2")


class TestDeriveKey:
    def test_derive_key_is_deterministic(self):
        key1 = derive_key(salt="somesalt", master_password="hunter2")
        key2 = derive_key(salt="somesalt", master_password="hunter2")
        assert key1 == key2

    def test_derive_key_differs_by_salt(self):
        key1 = derive_key(salt="salt-one", master_password="hunter2")
        key2 = derive_key(salt="salt-two", master_password="hunter2")
        assert key1 != key2

    def test_derive_key_differs_by_password(self):
        key1 = derive_key(salt="somesalt", master_password="hunter2")
        key2 = derive_key(salt="somesalt", master_password="other")
        assert key1 != key2

    def test_derive_key_returns_valid_urlsafe_b64_bytes(self):
        key = derive_key(salt="somesalt", master_password="hunter2")
        assert isinstance(key, bytes)
        # Must round-trip through urlsafe_b64decode without error, since
        # Fernet() requires exactly this encoding.
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32  # PBKDF2-HMAC-SHA256 digest size


class TestEncryptDecrypt:
    def test_roundtrip(self):
        key = derive_key(salt="somesalt", master_password="hunter2")
        cipher = encrypt(key=key, plaintext="my-secret-password")
        assert decrypt(key=key, cipher=cipher) == "my-secret-password"

    def test_ciphertext_is_not_plaintext(self):
        key = derive_key(salt="somesalt", master_password="hunter2")
        cipher = encrypt(key=key, plaintext="my-secret-password")
        assert cipher != "my-secret-password"

    def test_decrypt_with_wrong_key_fails(self):
        key = derive_key(salt="somesalt", master_password="hunter2")
        wrong_key = derive_key(salt="somesalt", master_password="different")
        cipher = encrypt(key=key, plaintext="my-secret-password")
        with pytest.raises(InvalidToken):
            decrypt(key=wrong_key, cipher=cipher)

    def test_encrypt_is_nondeterministic(self):
        # Fernet includes a random IV, so encrypting the same plaintext
        # twice with the same key must not produce identical ciphertext.
        key = derive_key(salt="somesalt", master_password="hunter2")
        cipher1 = encrypt(key=key, plaintext="my-secret-password")
        cipher2 = encrypt(key=key, plaintext="my-secret-password")
        assert cipher1 != cipher2
