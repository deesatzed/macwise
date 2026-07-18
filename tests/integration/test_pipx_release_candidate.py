import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[2]


def run(
    arguments: list[str], *, environment: dict[str, str], cwd: Path
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    return result


def test_release_wheel_installs_with_real_isolated_pipx(tmp_path: Path) -> None:
    (tmp_path / "user-home").mkdir()
    environment = dict(os.environ)
    environment.update(
        {
            "PIPX_HOME": str(tmp_path / "pipx-home"),
            "PIPX_BIN_DIR": str(tmp_path / "pipx-bin"),
            "PIPX_MAN_DIR": str(tmp_path / "pipx-man"),
            "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
            "PYTHONPATH": "",
            "HOME": str(tmp_path / "user-home"),
        }
    )
    distribution = tmp_path / "dist"
    run(
        ["uv", "build", "--wheel", "--out-dir", str(distribution)],
        environment=environment,
        cwd=ROOT,
    )
    wheel = next(distribution.glob("macwise-1.0.0rc1-*.whl"))

    run(
        [
            "uvx",
            "--from",
            "pipx",
            "pipx",
            "install",
            str(wheel),
            "--python",
            "3.12",
            "--force",
            "--backend",
            "pip",
        ],
        environment=environment,
        cwd=tmp_path,
    )
    executable = tmp_path / "pipx-bin" / "macwise"

    assert run([str(executable), "--version"], environment=environment, cwd=tmp_path).stdout == (
        "MacWise 1.0.0rc1\n"
    )
    assert (
        "What would you like to do?"
        in run([str(executable)], environment=environment, cwd=tmp_path).stdout
    )
    assert (
        "$macwise"
        in run(
            [str(executable), "setup", "codex", "--help"], environment=environment, cwd=tmp_path
        ).stdout
    )
    location = run(
        [
            str(executable),
            "codex",
            "serve",
            "--help",
        ],
        environment=environment,
        cwd=tmp_path,
    )
    assert location.returncode == 0
    assert str(ROOT) not in executable.resolve().as_posix()
