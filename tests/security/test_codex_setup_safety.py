import os
from pathlib import Path

from macwise.integration.setup import CodexCommandResult, CodexSetupService, SetupStatus

ROOT = Path(__file__).parents[2]
PAYLOAD = ROOT / "src" / "macwise" / "codex_payload" / "macwise"


class NeverRunner:
    def run(self, arguments: tuple[str, ...]) -> CodexCommandResult:
        raise AssertionError(f"Codex must not run: {arguments}")


def test_setup_refuses_symlinked_plugin_ancestor(tmp_path: Path) -> None:
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    home.mkdir()
    outside.mkdir()
    (home / "plugins").symlink_to(outside, target_is_directory=True)

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(os.__file__),
        runner=NeverRunner(),
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert not (outside / "macwise").exists()


def test_setup_refuses_symlinked_marketplace_file(tmp_path: Path) -> None:
    home = tmp_path / "home"
    outside = tmp_path / "outside.json"
    marketplace = home / ".agents" / "plugins" / "marketplace.json"
    marketplace.parent.mkdir(parents=True)
    outside.write_text("do not replace", encoding="utf-8")
    marketplace.symlink_to(outside)

    result = CodexSetupService(
        home=home,
        payload=PAYLOAD,
        python_executable=Path(os.__file__),
        runner=NeverRunner(),
    ).install()

    assert result.status is SetupStatus.REFUSED
    assert outside.read_text(encoding="utf-8") == "do not replace"


def test_setup_source_contains_no_shell_or_codex_config_write() -> None:
    source = (ROOT / "src" / "macwise" / "integration" / "setup.py").read_text(
        encoding="utf-8"
    )

    assert "shell=True" not in source
    assert ".codex/config.toml" not in source
    assert "rm -rf" not in source
