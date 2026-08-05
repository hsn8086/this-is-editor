"""Guards against source constructs that Nuitka cannot compile.

These failures never surface under ``uv run main.py``; they only appear after
packaging, so they can ship unnoticed. A cheap AST scan keeps them out of the
tree instead.
"""

import ast
from pathlib import Path

import pytest

PACKAGED_SOURCE_DIRS = ("pysrc", "tools")
project_root = Path(__file__).resolve().parents[3]


def _packaged_modules() -> list[Path]:
    """Collect every Python module that ends up inside the built binary."""
    return sorted(
        path
        for directory in PACKAGED_SOURCE_DIRS
        for path in (project_root / directory).rglob("*.py")
    )


@pytest.mark.parametrize("module_path", _packaged_modules(), ids=lambda p: p.name)
def test_module_avoids_pep695_type_parameters(module_path: Path) -> None:
    """PEP 695 type parameters break the packaged binary.

    Nuitka 2.7.12 does not implement the PEP 695 annotation scope, so a compiled
    ``def try_r[T](...)`` raises ``NameError: name 'T' is not defined`` while the
    module is imported. Use ``TypeVar`` until Nuitka supports the syntax.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    offenders = [
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node,
            ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        )
        and node.type_params
    ]

    assert not offenders, (
        f"{module_path.relative_to(project_root)} uses PEP 695 type parameters on "
        f"{offenders}, which Nuitka miscompiles. Use typing.TypeVar instead."
    )
