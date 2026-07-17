from collections.abc import Mapping, Sequence
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from macwise.system.commands import CommandState, ReadCommand, run_read_command


def test_runner_uses_fixed_executable_and_keeps_hostile_metadata_inert() -> None:
    captured: dict[str, object] = {}

    def fake_runner(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> CompletedProcess[bytes]:
        captured.update(
            args=tuple(args),
            shell=shell,
            check=check,
            capture_output=capture_output,
            timeout=timeout,
            env=dict(env),
        )
        return CompletedProcess(args, 0, stdout=b"safe output", stderr=b"")

    hostile_argument = "$(touch /tmp/macwise-injection)"
    result = run_read_command(
        ReadCommand.MDLS,
        ("-name", "kMDItemLastUsedDate", hostile_argument),
        timeout=2.5,
        source_environment={
            "HOME": "/Users/example",
            "LANG": "en_US.UTF-8",
            "SECRET_TOKEN": "do-not-forward",
        },
        runner=fake_runner,
        resolver=lambda _command: "/usr/bin/mdls",
    )

    assert result.state is CommandState.COMPLETE
    assert result.stdout == "safe output"
    assert captured["args"] == (
        "/usr/bin/mdls",
        "-name",
        "kMDItemLastUsedDate",
        hostile_argument,
    )
    assert captured["shell"] is False
    assert captured["check"] is False
    assert captured["capture_output"] is True
    assert captured["timeout"] == 2.5
    assert captured["env"] == {
        "HOME": "/Users/example",
        "HOMEBREW_NO_ANALYTICS": "1",
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "LANG": "en_US.UTF-8",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
    }


def test_missing_executable_is_an_explicit_unavailable_result() -> None:
    def runner_must_not_run(
        _args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> CompletedProcess[bytes]:
        raise AssertionError((shell, check, capture_output, timeout, env))

    result = run_read_command(
        ReadCommand.BREW,
        runner=runner_must_not_run,
        resolver=lambda _command: None,
    )

    assert result.state is CommandState.UNAVAILABLE
    assert result.return_code is None
    assert result.limitations == ("The brew read-only command is not available.",)


def test_timeout_is_returned_as_data_instead_of_escaping() -> None:
    def timing_out_runner(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> CompletedProcess[bytes]:
        del shell, check, capture_output, env
        raise TimeoutExpired(args, timeout, output=b"partial", stderr=b"still working")

    result = run_read_command(
        ReadCommand.DISKUTIL,
        ("list", "-plist"),
        timeout=0.25,
        runner=timing_out_runner,
        resolver=lambda _command: "/usr/sbin/diskutil",
    )

    assert result.state is CommandState.TIMED_OUT
    assert result.stdout == "partial"
    assert result.stderr == "still working"
    assert "timed out after 0.25 seconds" in result.limitations[0]


def test_nonzero_exit_and_invalid_utf8_are_preserved_safely() -> None:
    def failing_runner(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> CompletedProcess[bytes]:
        del shell, check, capture_output, timeout, env
        return CompletedProcess(args, 7, stdout=b"result\xff", stderr=b"problem\xfe")

    result = run_read_command(
        ReadCommand.MDLS,
        ("target",),
        runner=failing_runner,
        resolver=lambda _command: "/usr/bin/mdls",
    )

    assert result.state is CommandState.FAILED
    assert result.return_code == 7
    assert result.stdout == "result�"
    assert result.stderr == "problem�"
    assert "exited with status 7" in result.limitations[0]


def test_output_is_truncated_at_the_configured_byte_limit() -> None:
    def verbose_runner(
        args: Sequence[str],
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> CompletedProcess[bytes]:
        del shell, check, capture_output, timeout, env
        return CompletedProcess(args, 0, stdout=b"123456", stderr=b"abcdef")

    result = run_read_command(
        ReadCommand.MDLS,
        max_output_bytes=4,
        runner=verbose_runner,
        resolver=lambda _command: "/usr/bin/mdls",
    )

    assert result.stdout == "1234"
    assert result.stderr == "abcd"
    assert result.limitations == ("Command output was truncated to 4 bytes per stream.",)


def test_raw_program_names_and_invalid_bounds_are_rejected() -> None:
    with pytest.raises(ValueError, match="allowlisted ReadCommand"):
        run_read_command("rm", resolver=lambda _command: "/bin/rm")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timeout"):
        run_read_command(ReadCommand.MDLS, timeout=0)

    with pytest.raises(ValueError, match="max_output_bytes"):
        run_read_command(ReadCommand.MDLS, max_output_bytes=0)
