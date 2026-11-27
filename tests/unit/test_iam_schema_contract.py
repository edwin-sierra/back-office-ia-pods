from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.iam.models import User
from app.modules.iam.schemas import UserCreate, UserRead


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", f"{'a' * 320}@example.test"),
        ("full_name", "a" * 256),
        ("password_hash", "h" * 256),
    ],
)
def test_user_create_rejects_values_beyond_field_limits(field: str, value: str) -> None:
    user_data = {
        "email": "person@example.test",
        "full_name": "Test Person",
        "password_hash": "encoded-hash-placeholder",
    }

    with pytest.raises(ValidationError):
        UserCreate(**(user_data | {field: value}))


def test_user_read_serializes_all_profile_fields_and_excludes_credentials() -> None:
    user_id = uuid4()
    created_at = datetime(2026, 11, 27, tzinfo=UTC)
    updated_at = datetime(2026, 11, 28, tzinfo=UTC)
    user = User(
        id=user_id,
        email="person@example.test",
        full_name="Test Person",
        password_hash="encoded-hash-placeholder",
        is_active=False,
        created_at=created_at,
        updated_at=updated_at,
    )

    serialized = UserRead.model_validate(user).model_dump(mode="json")

    assert serialized == {
        "id": str(user_id),
        "email": "person@example.test",
        "full_name": "Test Person",
        "is_active": False,
        "created_at": "2026-11-27T00:00:00Z",
        "updated_at": "2026-11-28T00:00:00Z",
    }
    assert "password" not in serialized
    assert "password_hash" not in serialized
