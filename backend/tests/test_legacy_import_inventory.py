from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


EXPECTED_LEGACY_IMPORTS: set[tuple[str, str]] = {
    (
        "interfaces/runtime/session_person_manager_adapter.py",
        "session.session_person_manager",
    ),
    ("session/session_person_manager.py", "session.session_state"),
    ("session/session_person_manager.py", "session.station"),
    ("tests/test_app_runtime_headless.py", "session.session_state"),
    ("tests/test_domain_shims.py", "session.error_catalog"),
    ("tests/test_domain_shims.py", "session.error_normalizer"),
    ("tests/test_domain_shims.py", "session.rotation"),
    ("tests/test_domain_shims.py", "session.session_state"),
    ("tests/test_domain_shims.py", "session.session_sync"),
    ("tests/test_error_normalizer.py", "session.error_normalizer"),
    ("tests/test_main_runtime_contract.py", "session.rotation"),
    ("tests/test_main_runtime_contract.py", "session.session_snapshot"),
    ("tests/test_main_runtime_contract.py", "session.session_state"),
    ("tests/test_process_person_contract.py", "runtime.contracts"),
    ("tests/test_process_person_contract.py", "runtime.process_person"),
    ("tests/test_process_person_contract.py", "session.session_state"),
    ("tests/test_process_person_contract.py", "session.session_sync"),
    ("tests/test_process_person_contract.py", "session.station"),
    ("tests/test_process_person_shims.py", "runtime.contracts"),
    ("tests/test_process_person_shims.py", "runtime.process_person"),
    ("tests/test_rotate_stations_use_case.py", "session.session_state"),
    ("tests/test_rotation_runtime_integration.py", "session.session_person_manager"),
    ("tests/test_rotation_runtime_integration.py", "session.session_state"),
    ("tests/test_session_person_manager.py", "session.session_person_manager"),
    ("tests/test_session_person_manager.py", "session.session_state"),
    ("tests/test_session_person_manager_adapter.py", "session.session_person_manager"),
    ("tests/test_session_person_manager_adapter.py", "session.session_state"),
    ("tests/test_session_snapshot.py", "session.session_snapshot"),
    ("tests/test_session_snapshot.py", "session.session_state"),
    ("tests/test_session_snapshot_shim.py", "session.session_snapshot"),
    ("tests/test_session_snapshot_shim.py", "session.session_state"),
    ("tests/test_session_sync.py", "session.session_state"),
    ("tests/test_session_sync.py", "session.session_sync"),
    ("tests/test_versioning.py", "session.rotation"),
    ("tests/test_versioning.py", "session.session_state"),
    ("tests/test_websocket_contract_phase2.py", "session.session_state"),
}


def _iter_python_files(root: Path):
    excluded_parts = {"__pycache__", ".venv_movenet", "site-packages", ".git"}
    for path in root.rglob("*.py"):
        if any(part in excluded_parts for part in path.parts):
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        yield path


def _matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _is_legacy_import(module_name: str) -> bool:
    if _matches_prefix(module_name, "session"):
        return True
    return module_name in {"runtime.contracts", "runtime.process_person"}


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


def _collect_legacy_imports() -> set[tuple[str, str]]:
    imports: set[tuple[str, str]] = set()
    for path in _iter_python_files(BACKEND_ROOT):
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if _is_legacy_import(module_name):
                        imports.add((rel, module_name))
            elif isinstance(node, ast.ImportFrom):
                module_name = _resolve_import_from(path, node.module, node.level)
                if module_name and _is_legacy_import(module_name):
                    imports.add((rel, module_name))
    return imports


class LegacyImportInventoryTests(unittest.TestCase):
    def test_legacy_import_inventory_matches_baseline(self):
        observed = _collect_legacy_imports()
        missing = sorted(EXPECTED_LEGACY_IMPORTS - observed)
        added = sorted(observed - EXPECTED_LEGACY_IMPORTS)

        self.assertEqual(
            [],
            missing + added,
            msg=(
                "Legacy import inventory drift detected.\n"
                f"Missing entries: {missing}\n"
                f"Added entries: {added}"
            )
            if (missing or added)
            else None,
        )


if __name__ == "__main__":
    unittest.main()
