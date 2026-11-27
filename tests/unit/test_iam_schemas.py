from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.iam.models import User
from app.modules.iam.schemas import UserCreate, UserRead


def test_user_create_validates_email_and_defaults_to_active() -> None:
    user = UserCreate(
        email="person@example.test",
        full_name="Test Person",
        password_hash="encoded-hash-placeholder",
    )

    assert user.email == "person@example.test"
    assert user.is_active is True


@pytest.mark.parametrize("email", ["invalid", "person@localhost", "person @example.test", "a@b..c"])
def test_user_create_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email=email,
            full_name="Test Person",
            password_hash="encoded-hash-placeholder",
        )


def test_user_read_serializes_profile_without_password_hash() -> None:
    timestamp = datetime(2026, 11, 27, tzinfo=UTC)
    user = User(
        id=uuid4(),
        email="person@example.test",
        full_name="Test Person",
        password_hash="encoded-hash-placeholder",
        is_active=True,
        created_at=timestamp,
        updated_at=timestamp,
    )

    profile = UserRead.model_validate(user)
    serialized = profile.model_dump(mode="json")

    assert serialized["email"] == "person@example.test"
    assert serialized["full_name"] == "Test Person"
    assert serialized["is_active"] is True
    assert serialized["created_at"] == "2026-11-27T00:00:00Z"
    assert "password_hash" not in serialized
