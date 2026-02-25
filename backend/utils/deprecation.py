from __future__ import annotations

import warnings


def warn_legacy_module(*, module_name: str, replacement: str) -> None:
    warnings.warn(
        (
            f"{module_name} is deprecated and will be removed after Fase 2.4. "
            f"Use {replacement} instead."
        ),
        DeprecationWarning,
        stacklevel=2,
    )
