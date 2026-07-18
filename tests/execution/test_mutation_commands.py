import hashlib
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from macwise.execution.commands import (
    CommandActionError,
    MutationCommandAdapter,
    MutationExecutable,
    bounded_mutation_runner,
)


class RecordingRunner:
    def __init__(self, *, return_code: int = 0, stdout: bytes = b"ok") -> None:
        self.return_code = return_code
        self.stdout = stdout
        self.calls: list[tuple[tuple[str, ...], bool, bool, bool, float, Mapping[str, str]]] = []

    def __call__(
        self,
        args: Sequence[str],
        /,
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((tuple(args), shell, check, capture_output, timeout, dict(env)))
        return subprocess.CompletedProcess(
            args,
            self.return_code,
            stdout=self.stdout,
            stderr=b"synthetic error" if self.return_code else b"",
        )


def resolver(executable: MutationExecutable) -> str | None:
    return {
        MutationExecutable.BREW: "/opt/homebrew/bin/brew",
        MutationExecutable.LAUNCHCTL: "/bin/launchctl",
    }[executable]


def adapter(
    tmp_path: Path,
    runner: RecordingRunner,
) -> MutationCommandAdapter:
    launch_agents = tmp_path / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True)
    return MutationCommandAdapter(
        runner=runner,
        resolver=resolver,
        source_environment={"HOME": str(tmp_path), "PATH": "/hostile"},
        launch_agents_root=launch_agents,
        uid=501,
    )


def test_homebrew_methods_build_only_exact_allowlisted_argv_and_safe_environment(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)

    commands.uninstall_formula("ripgrep")
    commands.uninstall_cask("docker")
    commands.install_formula("ripgrep")
    commands.install_cask("docker")
    commands.stop_service("postgresql@17")
    commands.start_service("postgresql@17")

    assert [call[0] for call in runner.calls] == [
        ("/opt/homebrew/bin/brew", "uninstall", "--formula", "ripgrep"),
        ("/opt/homebrew/bin/brew", "uninstall", "--cask", "docker"),
        ("/opt/homebrew/bin/brew", "install", "--formula", "ripgrep"),
        ("/opt/homebrew/bin/brew", "install", "--cask", "docker"),
        ("/opt/homebrew/bin/brew", "services", "stop", "postgresql@17"),
        ("/opt/homebrew/bin/brew", "services", "start", "postgresql@17"),
    ]
    for _args, shell, check, capture_output, timeout, environment in runner.calls:
        assert shell is False
        assert check is False
        assert capture_output is True
        assert timeout == 30.0
        assert environment["HOMEBREW_NO_AUTO_UPDATE"] == "1"
        assert environment["HOMEBREW_NO_ANALYTICS"] == "1"
        assert environment["PATH"] != "/hostile"


def test_launch_agent_methods_use_exact_current_user_domain_and_safe_plist(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)
    plist = tmp_path / "Library" / "LaunchAgents" / "com.example.agent.plist"
    plist.write_bytes(b"synthetic")

    commands.disable_launch_agent(
        "com.example.agent",
        plist,
        was_running=True,
        expected_plist_sha256=hashlib.sha256(plist.read_bytes()).hexdigest(),
    )
    commands.enable_launch_agent(
        "com.example.agent",
        plist,
        was_running=True,
        expected_plist_sha256=hashlib.sha256(plist.read_bytes()).hexdigest(),
    )

    assert [call[0] for call in runner.calls] == [
        ("/bin/launchctl", "disable", "gui/501/com.example.agent"),
        ("/bin/launchctl", "bootout", "gui/501", str(plist)),
        ("/bin/launchctl", "enable", "gui/501/com.example.agent"),
        ("/bin/launchctl", "bootstrap", "gui/501", str(plist)),
    ]


def test_launch_agent_partial_restore_only_applies_missing_delta(tmp_path: Path) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)
    plist = tmp_path / "Library" / "LaunchAgents" / "com.example.agent.plist"
    plist.write_bytes(b"synthetic")

    commands.restore_launch_agent(
        "com.example.agent",
        plist,
        was_enabled=True,
        was_running=True,
        current_enabled=False,
        current_running=True,
        expected_plist_sha256=hashlib.sha256(plist.read_bytes()).hexdigest(),
    )

    assert [call[0] for call in runner.calls] == [
        ("/bin/launchctl", "enable", "gui/501/com.example.agent"),
    ]


@pytest.mark.parametrize(
    "token",
    ("--force", "name with spaces", "name\n--zap", "name\0zap", "../escape", ""),
)
def test_homebrew_methods_reject_flag_and_structure_injection(
    tmp_path: Path,
    token: str,
) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)

    with pytest.raises(CommandActionError, match="token"):
        commands.uninstall_formula(token)

    assert runner.calls == []


def test_nonzero_or_oversized_output_is_bounded_and_fails_closed(tmp_path: Path) -> None:
    runner = RecordingRunner(return_code=1, stdout=b"x" * 2_000_000)
    commands = adapter(tmp_path, runner)

    with pytest.raises(CommandActionError, match="did not complete") as captured:
        commands.uninstall_formula("ripgrep")

    assert "x" * 100 not in str(captured.value)
    assert len(runner.calls) == 1


def test_success_exit_with_oversized_output_still_fails_closed(tmp_path: Path) -> None:
    runner = RecordingRunner(stdout=b"x" * 2_000_000)
    commands = adapter(tmp_path, runner)

    with pytest.raises(CommandActionError, match="did not complete"):
        commands.uninstall_formula("ripgrep")


def test_default_mutation_runner_retains_only_bounded_output() -> None:
    completed = bounded_mutation_runner(
        (sys.executable, "-c", "import sys; sys.stdout.write('x' * 2000000)"),
        shell=False,
        check=False,
        capture_output=True,
        timeout=10.0,
        env={},
    )

    assert completed.returncode == 0
    assert len(completed.stdout) == (64 * 1024) + 1
    assert completed.stderr == b""


def test_resolver_cannot_substitute_a_discovered_executable(tmp_path: Path) -> None:
    runner = RecordingRunner()
    launch_agents = tmp_path / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True)
    commands = MutationCommandAdapter(
        runner=runner,
        resolver=lambda _executable: "/tmp/hostile-brew",
        source_environment={},
        launch_agents_root=launch_agents,
        uid=501,
    )

    with pytest.raises(CommandActionError, match="unavailable"):
        commands.uninstall_formula("ripgrep")

    assert runner.calls == []


@pytest.mark.parametrize("label", ("../agent", "agent/child", "agent\nchild", ""))
def test_launch_agent_rejects_unsafe_labels_without_running(
    tmp_path: Path,
    label: str,
) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)
    plist = tmp_path / "Library" / "LaunchAgents" / "agent.plist"
    plist.write_bytes(b"synthetic")

    with pytest.raises(CommandActionError, match="label"):
        commands.disable_launch_agent(
            label,
            plist,
            was_running=False,
            expected_plist_sha256=hashlib.sha256(plist.read_bytes()).hexdigest(),
        )

    assert runner.calls == []


def test_launch_agent_rejects_changed_plist_hash_before_any_command(tmp_path: Path) -> None:
    runner = RecordingRunner()
    commands = adapter(tmp_path, runner)
    plist = tmp_path / "Library" / "LaunchAgents" / "agent.plist"
    plist.write_bytes(b"changed")

    with pytest.raises(CommandActionError, match="content changed"):
        commands.disable_launch_agent(
            "com.example.agent",
            plist,
            was_running=True,
            expected_plist_sha256="a" * 64,
        )

    assert runner.calls == []
