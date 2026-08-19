import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-123", "investor")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "investor"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token("user-123", "admin")
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["exp"] > payload["iat"]


def test_decode_rejects_tampered_token():
    token = create_access_token("user-123", "investor")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(ValueError):
        decode_token(tampered)


def test_decode_rejects_garbage():
    with pytest.raises(ValueError):
        decode_token("not.a.jwt")
