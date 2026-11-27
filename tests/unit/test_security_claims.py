from datetime import UTC, datetime
from uuid import uuid4

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings
from app.core.security import decode_token


def test_decoded_token_exposes_validated_issued_and_expiration_times() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    subject = uuid4()
    issued_at = 1_700_000_000
    expires_at = 4_000_000_000
    token = jwt.encode(
        {
            "sub": str(subject),
            "iat": issued_at,
            "exp": expires_at,
            "type": "access",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    claims = decode_token(token, settings, "access")

    assert claims.subject == subject
    assert claims.token_type == "access"
    assert claims.issued_at == datetime.fromtimestamp(issued_at, UTC)
    assert claims.expires_at == datetime.fromtimestamp(expires_at, UTC)


def test_decode_token_rejects_boolean_issued_at_timestamp() -> None:
    settings = Settings(jwt_secret_key="unit-test-signing-key-with-sufficient-length")
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": True,
            "exp": 4_000_000_000,
            "type": "access",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(token, settings, "access")
