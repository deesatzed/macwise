import asyncio
import os
import subprocess
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from macwise.integration.models import Operation

ROOT = Path(__file__).parents[2]


def run_checked(arguments: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_built_wheel_contains_valid_plugin_and_serves_stdio(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["UV_CACHE_DIR"] = str(tmp_path / "uv-cache")
    distribution = tmp_path / "dist"
    environment_dir = tmp_path / "venv"
    run_checked(["uv", "build", "--wheel", "--out-dir", str(distribution)], env=environment)
    wheel = next(distribution.glob("macwise-*.whl"))
    run_checked(["uv", "venv", "--python", "3.12", str(environment_dir)], env=environment)
    python = environment_dir / "bin" / "python"
    run_checked(
        ["uv", "pip", "install", "--python", str(python), "--no-cache", str(wheel)],
        env=environment,
    )
    payload_check = run_checked(
        [
            str(python),
            "-c",
            (
                "from importlib.resources import files; "
                "p=files('macwise').joinpath('codex_payload','macwise'); "
                "assert p.joinpath('.codex-plugin','plugin.json').is_file(); "
                "assert p.joinpath('.mcp.json').is_file(); print(p)"
            ),
        ],
        env=environment,
    )
    assert "codex_payload/macwise" in payload_check.stdout
    executable = environment_dir / "bin" / "macwise"
    help_result = run_checked([str(executable), "setup", "codex", "--help"], env=environment)
    assert "$macwise" in help_result.stdout

    async def list_installed_tools() -> set[str]:
        stderr_path = tmp_path / "installed-server.stderr"
        parameters = StdioServerParameters(
            command=str(executable),
            args=["codex", "serve"],
            env={"HOME": str(tmp_path / "isolated-home")},
        )
        with stderr_path.open("w+", encoding="utf-8") as stderr:
            async with (
                stdio_client(parameters, errlog=stderr) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                tools = await session.list_tools()
            stderr.seek(0)
            assert "traceback" not in stderr.read().casefold()
        return {tool.name for tool in tools.tools}

    assert asyncio.run(list_installed_tools()) == {operation.value for operation in Operation}
