from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _iter_python_files(root: Path):
    excluded_parts = {
        "__pycache__",
        ".venv_movenet",
        "site-packages",
        ".git",
    }
    for path in root.rglob("*.py"):
        if any(part in excluded_parts for part in path.parts):
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        yield path


def _iter_imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_import_from(path, node.module, node.level)
            if module_name:
                yield module_name, node.lineno


def _matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _resolve_import_from(path: Path, module: str | None, level: int) -> str:
    if level <= 0:
        return module or ""

    rel = path.relative_to(BACKEND_ROOT)
    pkg_parts = list(rel.with_suffix("").parts[:-1])
    if level == 1:
        base_parts = pkg_parts
    else:
        trim = level - 1
        base_parts = pkg_parts[:-trim] if trim <= len(pkg_parts) else []

    if module:
        return ".".join(base_parts + module.split("."))
    return ".".join(base_parts)


LEGACY_EXACT_MODULES = {
    "runtime.contracts",
    "runtime.process_person",
    "session_snapshot",
    "session_state",
    "session_sync",
    "rotation",
    "error_catalog",
    "error_normalizer",
    "session_person_manager",
    "station",
}


def _is_legacy_import(module_name: str) -> bool:
    if _matches_prefix(module_name, "session"):
        return True
    return any(
        _matches_prefix(module_name, legacy_module)
        for legacy_module in LEGACY_EXACT_MODULES
    )


class LayerBoundariesTests(unittest.TestCase):
    def test_domain_does_not_depend_on_outer_layers_or_io_frameworks(self):
        forbidden_prefixes = (
            "application",
            "communication",
            "runtime",
            "infrastructure",
            "interfaces",
            "video",
            "detectors",
            "tracking",
            "session",
            "websockets",
            "cv2",
        )
        violations: list[str] = []
        for path in _iter_python_files(BACKEND_ROOT / "domain"):
            for module_name, line in _iter_imports(path):
                if any(
                    _matches_prefix(module_name, prefix)
                    for prefix in forbidden_prefixes
                ):
                    rel = path.relative_to(BACKEND_ROOT)
                    violations.append(f"{rel}:{line} -> {module_name}")

        self.assertEqual(
            [],
            violations,
            msg=(
                "Domain layer imports forbidden dependencies:\n- "
                + "\n- ".join(violations)
            )
            if violations
            else None,
        )

    def test_application_does_not_depend_on_runtime_transport_or_vision_layers(self):
        forbidden_prefixes = (
            "communication",
            "runtime",
            "infrastructure",
            "interfaces",
            "video",
            "detectors",
            "tracking",
            "session",
            "websockets",
            "cv2",
        )
        violations: list[str] = []
        for path in _iter_python_files(BACKEND_ROOT / "application"):
            for module_name, line in _iter_imports(path):
                if any(
                    _matches_prefix(module_name, prefix)
                    for prefix in forbidden_prefixes
                ):
                    rel = path.relative_to(BACKEND_ROOT)
                    violations.append(f"{rel}:{line} -> {module_name}")

        self.assertEqual(
            [],
            violations,
            msg=(
                "Application layer imports forbidden dependencies:\n- "
                + "\n- ".join(violations)
            )
            if violations
            else None,
        )

    def test_main_is_unique_production_import_site_for_communication_bootstrap(self):
        bootstrap_modules = {
            "communication.websocket_server",
        }
        violations: list[str] = []

        for path in _iter_python_files(BACKEND_ROOT):
            if BACKEND_ROOT / "tests" in path.parents:
                continue
            rel = path.relative_to(BACKEND_ROOT)
            if rel.as_posix() == "main.py":
                continue
            for module_name, line in _iter_imports(path):
                if module_name in bootstrap_modules:
                    violations.append(f"{rel}:{line} -> {module_name}")

        self.assertEqual(
            [],
            violations,
            msg=(
                "Only main.py should import communication bootstrap module(s):\n- "
                + "\n- ".join(violations)
            )
            if violations
            else None,
        )

    def test_no_legacy_imports_anywhere_in_backend(self):
        violations: list[str] = []

        for path in _iter_python_files(BACKEND_ROOT):
            rel = path.relative_to(BACKEND_ROOT).as_posix()
            for module_name, line in _iter_imports(path):
                if not _is_legacy_import(module_name):
                    continue
                violations.append(f"{rel}:{line} -> {module_name}")

        self.assertEqual(
            [],
            violations,
            msg=(
                "Legacy imports are forbidden in all backend modules:\n- "
                + "\n- ".join(violations)
            )
            if violations
            else None,
        )


if __name__ == "__main__":
    unittest.main()
