"""Secret store tests (Sprint 11) — encryption, integrity, masking, fallback."""

import pytest

from app.core.secrets import SecretBox, mask_secret


def test_encrypt_decrypt_round_trip():
    box = SecretBox("unit-test-key")
    token = box.encrypt("sk-ant-abc123456789")
    assert token != "sk-ant-abc123456789"
    assert "abc123" not in token  # ciphertext hides the plaintext
    assert box.decrypt(token) == "sk-ant-abc123456789"


def test_ciphertext_is_nondeterministic():
    box = SecretBox("unit-test-key")
    assert box.encrypt("same-secret-value") != box.encrypt("same-secret-value")


def test_wrong_key_cannot_decrypt():
    a = SecretBox("key-a-aaaaaaaa")
    b = SecretBox("key-b-bbbbbbbb")
    token = a.encrypt("top-secret-value")
    with pytest.raises(Exception):
        b.decrypt(token)


def test_stdlib_fallback_round_trip_and_tamper():
    box = SecretBox("fallback-key")
    box._fernet = None  # force the stdlib authenticated cipher
    token = box.encrypt("fallback-secret-9999")
    assert token.startswith("wes1:")
    assert box.decrypt(token) == "fallback-secret-9999"
    # Tampering with the ciphertext is detected.
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    with pytest.raises(ValueError):
        box.decrypt(tampered)


def test_mask_secret():
    assert mask_secret(None) is None
    assert mask_secret("") is None
    assert mask_secret("abcd") == "***"
    assert mask_secret("sk-ant-1234").endswith("1234")
    assert "sk-ant" not in mask_secret("sk-ant-1234")
