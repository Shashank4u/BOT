"""Security utilities unit tests."""

from app.core.security import get_password_hash, verify_password


def test_password_hashing() -> None:
    password = "SecureP@ssw0rd!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False
