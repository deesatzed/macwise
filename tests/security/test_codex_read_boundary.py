import ast
from pathlib import Path

INTEGRATION_ROOT = Path(__file__).parents[2] / "src" / "macwise" / "integration"
FORBIDDEN_MODULES = {
    "macwise.execution",
    "macwise.persistence",
    "macwise.services.approval",
    "macwise.services.execution",
    "macwise.services.revalidation",
}
FORBIDDEN_NAMES = {"ExecutionStore", "PlanStore", "StateLock"}


def test_codex_integration_has_no_mutation_or_state_store_imports() -> None:
    violations: list[str] = []
    for path in sorted(INTEGRATION_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(
                        alias.name == forbidden or alias.name.startswith(f"{forbidden}.")
                        for forbidden in FORBIDDEN_MODULES
                    ):
                        violations.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if any(
                    module == forbidden or module.startswith(f"{forbidden}.")
                    for forbidden in FORBIDDEN_MODULES
                ):
                    violations.append(f"{path.name}: from {module}")
                for alias in node.names:
                    if alias.name in FORBIDDEN_NAMES:
                        violations.append(f"{path.name}: import {alias.name}")

    assert violations == []


def test_codex_integration_defines_no_generic_dispatch_or_mutation_tool_names() -> None:
    forbidden = {"dispatch", "shell", "execute", "apply", "undo", "approve"}
    discovered: set[str] = set()
    for path in sorted(INTEGRATION_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        discovered.update(
            node.name.casefold()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

    assert discovered.isdisjoint(forbidden)
