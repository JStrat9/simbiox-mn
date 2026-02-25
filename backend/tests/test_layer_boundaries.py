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
            if node.module:
                yield node.module, node.lineno


def _matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _is_legacy_import(module_name: str) -> bool:
    if _matches_prefix(module_name, "session"):
        return True
    return module_name in {"runtime.contracts", "runtime.process_person"}


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

    def test_production_modules_do_not_import_legacy_shim_modules(self):
        allowed_legacy_import_sites = {
            ("main.py", "session.session_person_manager"),
            ("runtime/app_runtime.py", "session.session_person_manager"),
        }
        excluded_roots = {
            BACKEND_ROOT / "tests",
            BACKEND_ROOT / "session",
        }
        violations: list[str] = []

        for path in _iter_python_files(BACKEND_ROOT):
            if any(root in path.parents or path == root for root in excluded_roots):
                continue
            rel = path.relative_to(BACKEND_ROOT).as_posix()
            for module_name, line in _iter_imports(path):
                if not _is_legacy_import(module_name):
                    continue
                if (rel, module_name) in allowed_legacy_import_sites:
                    continue
                violations.append(f"{rel}:{line} -> {module_name}")

        self.assertEqual(
            [],
            violations,
            msg=(
                "Production modules imported non-allowlisted legacy modules:\n- "
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


if __name__ == "__main__":
    unittest.main()
