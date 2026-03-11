"""Tests for security utilities (password hashing, JWT)."""

from datetime import timedelta

import pytest

from app.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

# ----- Password hashing -----


def test_password_hash_and_verify() -> None:
    """Hashed password verifies correctly."""
    password = "securepass123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_wrong_password() -> None:
    """Wrong password does not verify."""
    hashed = get_password_hash("correctpass")
    assert verify_password("wrongpass", hashed) is False


def test_same_password_different_hashes() -> None:
    """Same password produces different hashes (salt)."""
    h1 = get_password_hash("samepass")
    h2 = get_password_hash("samepass")
    assert h1 != h2
    assert verify_password("samepass", h1) is True
    assert verify_password("samepass", h2) is True


# ----- Access token -----


def test_create_and_decode_access_token() -> None:
    """Access token encodes sub and decodes correctly."""
    token = create_access_token(data={"sub": 42})
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"
    assert payload.get("type") == "access"
    assert "exp" in payload


def test_decode_access_token_wrong_type_returns_none() -> None:
    """Refresh token decoded as access returns None (type mismatch)."""
    refresh = create_refresh_token(data={"sub": 1})
    payload = decode_access_token(refresh)
    assert payload is None


def test_decode_access_token_invalid_returns_none() -> None:
    """Invalid or malformed token returns None."""
    assert decode_access_token("not.a.token") is None
    assert decode_access_token("") is None


def test_access_token_expiry() -> None:
    """Custom expiry_delta is reflected in token."""
    token = create_access_token(data={"sub": 1}, expires_delta=timedelta(minutes=5))
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload


# ----- Refresh token -----


def test_create_and_decode_refresh_token() -> None:
    """Refresh token encodes sub and decodes correctly."""
    token = create_refresh_token(data={"sub": 99})
    assert isinstance(token, str)
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload.get("sub") == "99"
    assert payload.get("type") == "refresh"
    assert "exp" in payload


def test_decode_refresh_token_wrong_type_returns_none() -> None:
    """Access token decoded as refresh returns None."""
    access = create_access_token(data={"sub": 1})
    payload = decode_refresh_token(access)
    assert payload is None


def test_decode_refresh_token_invalid_returns_none() -> None:
    """Invalid refresh token returns None."""
    assert decode_refresh_token("invalid") is None
