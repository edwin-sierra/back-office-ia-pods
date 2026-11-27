from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_argon2id_and_not_reversible() -> None:
    password = "correct-horse-battery-staple"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash)
    assert not verify_password("incorrect-password", password_hash)


def test_access_token_has_required_claims_and_fifteen_minute_lifetime() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    subject = uuid4()

    token = create_access_token(subject, settings)
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    claims = decode_token(token, settings, "access")

    assert payload["sub"] == str(subject)
    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == 15 * 60
    assert claims.subject == subject
    assert claims.token_type == "access"


def test_refresh_token_has_seven_day_lifetime() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")

    token = create_refresh_token(uuid4(), settings)
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["type"] == "refresh"
    assert payload["exp"] - payload["iat"] == 7 * 24 * 60 * 60


def test_decode_token_rejects_malformed_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token(
            "not-a-jwt",
            Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length"),
            "access",
        )


def test_decode_token_rejects_expired_token() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    issued_at = datetime.now(UTC) - timedelta(minutes=2)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": issued_at,
            "exp": issued_at + timedelta(minutes=1),
            "type": "access",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(token, settings, "access")


def test_decode_token_rejects_wrong_type() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")

    with pytest.raises(InvalidTokenError):
        decode_token(create_refresh_token(uuid4(), settings), settings, "access")


def test_decode_token_rejects_invalid_subject() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": "not-a-uuid", "iat": now, "exp": now + timedelta(minutes=1), "type": "access"},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError, match="subject"):
        decode_token(token, settings, "access")


def test_security_operations_do_not_log_credentials_or_tokens(
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    password = "unit-test-password"
    token = create_access_token(uuid4(), settings)

    verify_password(password, hash_password(password))
    decode_token(token, settings, "access")

    assert password not in caplog.text
    assert token not in caplog.text
