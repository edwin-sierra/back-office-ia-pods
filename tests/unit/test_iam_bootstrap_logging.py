import builtins
import sys
from unittest.mock import Mock

import pytest

from app.modules.iam import bootstrap


def test_bootstrap_command_does_not_log_or_display_entered_password(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    password = "bootstrap-test-password"
    getpass_prompt = Mock(return_value=password)
    input_prompt = Mock(side_effect=AssertionError("bootstrap must not use input()"))

    async def create_user(email: str, full_name: str, received_password: str) -> bool:
        assert email == "admin@example.test"
        assert full_name == "Initial Admin"
        assert received_password == password
        return True

    monkeypatch.setattr(bootstrap, "_create_user", create_user)
    monkeypatch.setattr("getpass.getpass", getpass_prompt)
    monkeypatch.setattr(builtins, "input", input_prompt)
    monkeypatch.setattr(
        sys,
        "argv",
        ["bootstrap", "--email", "admin@example.test", "--full-name", "Initial Admin"],
    )

    bootstrap.main()

    output = capsys.readouterr()
    getpass_prompt.assert_called_once_with("Contraseña: ")
    input_prompt.assert_not_called()
    assert password not in output.out
    assert password not in output.err
    assert password not in caplog.text
