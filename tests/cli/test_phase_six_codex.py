from dataclasses import dataclass

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.integration.setup import SetupResult, SetupStatus

RUNNER = CliRunner()


@dataclass
class FakeSetupService:
    result: SetupResult
    calls: int = 0

    def install(self) -> SetupResult:
        self.calls += 1
        return self.result


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (SetupStatus.INSTALLED, "installed"),
        (SetupStatus.UPDATED, "updated"),
        (SetupStatus.ALREADY_CURRENT, "already current"),
    ],
)
def test_setup_codex_reports_success_and_one_plain_next_step(
    monkeypatch: pytest.MonkeyPatch,
    status: SetupStatus,
    expected: str,
) -> None:
    service = FakeSetupService(SetupResult(status=status, message="setup complete"))
    monkeypatch.setattr(cli, "_codex_setup_factory", lambda: service)

    result = RUNNER.invoke(cli.app, ["setup", "codex"])

    assert result.exit_code == 0
    assert expected in result.stdout.casefold()
    assert "new Codex session" in result.stdout
    assert "$macwise" in result.stdout
    assert "MCP" not in result.stdout
    assert "marketplace" not in result.stdout.casefold()
    assert service.calls == 1


def test_setup_codex_refusal_is_nonzero_and_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeSetupService(
        SetupResult(
            status=SetupStatus.REFUSED,
            message="Codex is unavailable.",
            recovery="Install or update Codex, then retry.",
        )
    )
    monkeypatch.setattr(cli, "_codex_setup_factory", lambda: service)

    result = RUNNER.invoke(cli.app, ["setup", "codex"])

    assert result.exit_code == 2
    assert "Codex is unavailable." in result.stdout
    assert "Install or update Codex" in result.stdout


def test_hidden_codex_server_entry_point_runs_injected_stdio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(cli, "_codex_stdio_runner", lambda: calls.append("stdio"))

    result = RUNNER.invoke(cli.app, ["codex", "serve"])

    assert result.exit_code == 0
    assert result.stdout == ""
    assert calls == ["stdio"]


def test_internal_codex_command_is_hidden_from_public_root_help() -> None:
    result = RUNNER.invoke(cli.app, ["--help"])
    setup_help = RUNNER.invoke(cli.app, ["setup", "--help"])

    assert result.exit_code == 0
    assert "codex serve" not in result.stdout.casefold()
    assert setup_help.exit_code == 0
    assert "codex" in setup_help.stdout.casefold()
