from argon2 import PasswordHasher
import hashlib
import base64

from cryptography.fernet import Fernet


def hash_password(password: str) -> str:
    ph: PasswordHasher = PasswordHasher()
    hashed: str = ph.hash(password=password)
    return hashed


def verify_password(stored_hash: str, attempted: str) -> bool:
    ph: PasswordHasher = PasswordHasher()
    try:
        return ph.verify(stored_hash, attempted)
    except Exception:
        return False


def derive_key(salt: str, master_password: str) -> bytes:
    key: bytes = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=master_password.encode(),
        salt=salt.encode(),
        iterations=600000,
    )
    return base64.urlsafe_b64encode(key)


def encrypt(key: bytes, plaintext: str) -> str:
    fernet: Fernet = Fernet(key=key)
    encrypted: bytes = fernet.encrypt(data=plaintext.encode())
    return encrypted.decode()


def decrypt(key: bytes, cipher: str) -> str:
    fernet: Fernet = Fernet(key=key)
    decrypted: bytes = fernet.decrypt(token=cipher)
    return decrypted.decode()
