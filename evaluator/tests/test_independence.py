"""The evaluator must remain a technically independent side application."""

import ast
from pathlib import Path

from macwise_eval.cli import app

EVALUATOR_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = EVALUATOR_ROOT / "src" / "macwise_eval"


def test_cli_application_is_available_without_product_imports() -> None:
    """The evaluator exposes its own command surface and never imports MacWise."""
    assert app.info.name == "macwise-eval"

    source_files = tuple(sorted(SOURCE_ROOT.rglob("*.py")))
    assert source_files, "the evaluator must contain its own source files"

    forbidden: list[str] = []
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
                if any(name == "macwise" or name.startswith("macwise.") for name in names):
                    forbidden.append(f"{path.relative_to(EVALUATOR_ROOT)} imports {names}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "macwise" or module.startswith("macwise."):
                    forbidden.append(f"{path.relative_to(EVALUATOR_ROOT)} imports {module}")

    assert not forbidden, "Evaluator imports production code: " + "; ".join(forbidden)


def test_evaluator_source_never_executes_or_path_injects_the_product() -> None:
    """Serialized files, not product execution or source paths, are the only boundary."""
    forbidden_fragments = (
        "sys.path.insert",
        "sys.path.append",
        '"macwise"',
        "'macwise'",
        "src/macwise",
    )

    findings: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            if fragment in text:
                findings.append(f"{path.relative_to(EVALUATOR_ROOT)} contains {fragment!r}")

    assert not findings, "Evaluator crosses the product boundary: " + "; ".join(findings)
