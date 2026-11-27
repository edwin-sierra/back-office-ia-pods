import sys

from app.modules.iam import bootstrap


def test_bootstrap_command_does_not_log_or_display_entered_password(
    monkeypatch, capsys, caplog
) -> None:
    password = "bootstrap-test-password"

    async def create_user(email: str, full_name: str, received_password: str) -> bool:
        assert email == "admin@example.test"
        assert full_name == "Initial Admin"
        assert received_password == password
        return True

    monkeypatch.setattr(bootstrap, "_create_user", create_user)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda _: password)
    monkeypatch.setattr(
        sys,
        "argv",
        ["bootstrap", "--email", "admin@example.test", "--full-name", "Initial Admin"],
    )

    bootstrap.main()

    output = capsys.readouterr()
    assert password not in output.out
    assert password not in output.err
    assert password not in caplog.text
