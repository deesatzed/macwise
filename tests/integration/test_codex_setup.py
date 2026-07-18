import json
import subprocess
import sys
from collections import deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from macwise.integration.setup import (
    CodexCommandResult,
    CodexSetupService,
    SetupStatus,
    SubprocessCodexRunner,
)

ROOT = Path(__file__).parents[2]
PAYLOAD = ROOT / "src" / "macwise" / "codex_payload" / "macwise"


class FakeCodexRunner:
    def __init__(self, *results: CodexCommandResult) -> None:
        self.results = deque(results or (CodexCommandResult(ok=True, stdout='{"installed":true}'),))
        self.calls: list[tuple[str, ...]] = []

    def run(self, arguments: tuple[str, ...]) -> CodexCommandResult:
        self.calls.append(arguments)
        return self.results.popleft()


def make_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def marketplace(home: Path) -> dict[str, object]:
    return json.loads(
        (home / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )


def test_fresh_setup_installs_owned_personal_plugin_with_absolute_runtime(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    runtime = tmp_path / "Python Runtime" / "python3"
    runtime.parent.mkdir()
    runtime.write_text("synthetic executable", encoding="utf-8")
    runtime.chmod(0o700)
    runner = FakeCodexRunner()

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=runtime,
        runner=runner,
    ).install()

    installed = home / "plugins" / "macwise"
    mcp = json.loads((installed / ".mcp.json").read_text(encoding="utf-8"))
    assert result.status is SetupStatus.INSTALLED
    assert (installed / ".macwise-owned.json").is_file()
    assert mcp["mcpServers"]["macwise"] == {
        "command": str(runtime.resolve()),
        "args": ["-m", "macwise", "codex", "serve"],
    }
    document = marketplace(home)
    assert document["name"] == "personal"
    assert document["interface"] == {"displayName": "Personal"}
    assert document["plugins"] == [
        {
            "name": "macwise",
            "source": {"source": "local", "path": "./plugins/macwise"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }
    ]
    assert runner.calls == [("plugin", "add", "macwise@personal", "--json")]


def test_setup_preserves_marketplace_metadata_order_and_unrelated_entries(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    path = home / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True)
    other = {
        "name": "other",
        "source": {"source": "local", "path": "./plugins/other"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
        "category": "Developer Tools",
    }
    path.write_text(
        json.dumps(
            {
                "name": "my-personal",
                "interface": {"displayName": "My Plugins", "theme": "kept"},
                "plugins": [other],
                "futureField": {"preserve": True},
            }
        ),
        encoding="utf-8",
    )
    runner = FakeCodexRunner()

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    document = marketplace(home)
    plugins = cast(list[dict[str, object]], document["plugins"])
    assert result.status is SetupStatus.INSTALLED
    assert document["interface"] == {"displayName": "My Plugins", "theme": "kept"}
    assert document["futureField"] == {"preserve": True}
    assert plugins[0] == other
    assert plugins[1]["name"] == "macwise"
    assert runner.calls[-1] == ("plugin", "add", "macwise@my-personal", "--json")


def test_same_payload_and_runtime_are_idempotent(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    runner = FakeCodexRunner(
        CodexCommandResult(ok=True, stdout='{"installed":true}'),
        CodexCommandResult(ok=True, stdout='{"installed":true}'),
    )
    service = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    )

    first = service.install()
    before = (home / "plugins" / "macwise" / ".macwise-owned.json").read_bytes()
    second = service.install()
    after = (home / "plugins" / "macwise" / ".macwise-owned.json").read_bytes()

    assert first.status is SetupStatus.INSTALLED
    assert second.status is SetupStatus.ALREADY_CURRENT
    assert before == after
    assert len(runner.calls) == 2


def test_setup_refuses_unowned_existing_plugin_without_running_codex(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    foreign = home / "plugins" / "macwise"
    foreign.mkdir(parents=True)
    (foreign / "notes.txt").write_text("belongs to the user", encoding="utf-8")
    runner = FakeCodexRunner()

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert "owned" in result.message.casefold()
    assert (foreign / "notes.txt").read_text(encoding="utf-8") == "belongs to the user"
    assert runner.calls == []


def test_setup_refuses_foreign_same_name_marketplace_source(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    path = home / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "name": "personal",
                "interface": {"displayName": "Personal"},
                "plugins": [
                    {
                        "name": "macwise",
                        "source": {"source": "git", "url": "https://example.invalid/other"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
                        "category": "Other",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    before = path.read_bytes()
    runner = FakeCodexRunner()

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert "marketplace" in result.message.casefold()
    assert path.read_bytes() == before
    assert runner.calls == []


def test_fresh_failed_codex_install_compensates_files_and_selector(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    runner = FakeCodexRunner(
        CodexCommandResult(ok=False, stderr="install failed"),
        CodexCommandResult(ok=True, stdout='{"removed":true}'),
    )

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert not (home / "plugins" / "macwise").exists()
    assert not (home / ".agents" / "plugins" / "marketplace.json").exists()
    assert runner.calls == [
        ("plugin", "add", "macwise@personal", "--json"),
        ("plugin", "remove", "macwise@personal", "--json"),
    ]


def test_failed_compensation_is_reported_as_interrupted(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    runner = FakeCodexRunner(
        CodexCommandResult(ok=False, stderr="install failed"),
        CodexCommandResult(ok=False, stderr="remove failed"),
    )

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    assert result.status is SetupStatus.INTERRUPTED
    assert "retry" in result.recovery.casefold()


def test_setup_rejects_unverifiable_codex_success_output(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    runner = FakeCodexRunner(
        CodexCommandResult(ok=True, stdout="not-json"),
        CodexCommandResult(ok=True, stdout='{"removed":true}'),
    )

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(sys.executable),
        runner=runner,
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert "verify" in result.message.casefold()
    assert not (home / "plugins" / "macwise").exists()


def test_subprocess_runner_uses_fixed_executable_safe_env_and_no_shell(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text("synthetic", encoding="utf-8")
    executable.chmod(0o700)
    captured: dict[str, object] = {}

    def fake_process(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> subprocess.CompletedProcess[bytes]:
        captured.update(
            args=tuple(args),
            shell=shell,
            check=check,
            capture_output=capture_output,
            timeout=timeout,
            env=dict(env),
        )
        return subprocess.CompletedProcess(args, 0, stdout=b'{"installed":true}', stderr=b"")

    runner = SubprocessCodexRunner(
        executable=executable,
        home=tmp_path,
        process_runner=fake_process,
        source_environment={"LANG": "en_US.UTF-8", "SECRET": "not-forwarded"},
    )

    result = runner.run(("plugin", "add", "macwise@personal", "--json"))

    assert result.ok is True
    assert captured["args"] == (
        str(executable.resolve()),
        "plugin",
        "add",
        "macwise@personal",
        "--json",
    )
    assert captured["shell"] is False
    assert captured["check"] is False
    assert captured["capture_output"] is True
    assert captured["env"] == {
        "HOME": str(tmp_path),
        "LANG": "en_US.UTF-8",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
    }


def test_subprocess_runner_rejects_every_non_setup_command(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text("synthetic", encoding="utf-8")
    executable.chmod(0o700)
    runner = SubprocessCodexRunner(executable=executable, home=tmp_path)

    result = runner.run(("exec", "rm", "-rf"))

    assert result.ok is False
    assert "allowlisted" in result.stderr.casefold()


def test_subprocess_runner_rejects_truncated_codex_output(tmp_path: Path) -> None:
    executable = tmp_path / "codex"
    executable.write_text("synthetic", encoding="utf-8")
    executable.chmod(0o700)

    def noisy_process(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> subprocess.CompletedProcess[bytes]:
        del shell, check, capture_output, timeout, env
        return subprocess.CompletedProcess(args, 0, stdout=b"x" * 70_000, stderr=b"")

    runner = SubprocessCodexRunner(
        executable=executable,
        home=tmp_path,
        process_runner=noisy_process,
    )

    result = runner.run(("plugin", "add", "macwise@personal", "--json"))

    assert result.ok is False
    assert len(result.stdout.encode()) <= 65_536
    assert "output limit" in result.stderr.casefold()
