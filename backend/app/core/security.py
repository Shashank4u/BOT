"""Security utilities — password hashing and secret encryption helpers."""

import base64
import hashlib

import bcrypt
from cryptography.fernet import Fernet, InvalidToken


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _fernet(secret_key: str) -> Fernet:
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plain_text: str, secret_key: str) -> str:
    """Encrypt a broker password for reversible storage."""
    return _fernet(secret_key).encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(cipher_text: str, secret_key: str) -> str:
    """Decrypt a stored broker password."""
    try:
        return _fernet(secret_key).decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt stored credentials") from exc
