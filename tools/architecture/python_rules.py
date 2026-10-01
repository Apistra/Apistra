"""AST-based architecture rules that complement Import Linter.

The checker has no third-party runtime dependency so it can also validate
retained positive and negative fixtures.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

LAYER_ALLOWED_DEPENDENCIES = {
    "domain": {"domain"},
    "ports": {"domain", "ports"},
    "application": {"domain", "ports", "application"},
    "adapters": {"domain", "ports", "application", "adapters"},
}

DOMAIN_FORBIDDEN_PREFIXES = (
    "fastapi",
    "openai",
    "pydantic",
    "qdrant_client",
    "sqlalchemy",
    "temporalio",
)


@dataclass(frozen=True, slots=True)
class Violation:
    rule: str
    path: Path
    line: int
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.message}"


def _imports(
    tree: ast.AST,
    path: Path,
    source_root: Path,
) -> Iterable[tuple[str, tuple[str, ...], int]]:
    relative = path.relative_to(source_root).with_suffix("")
    package_parts = list(relative.parts[:-1])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, (), node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                imported = node.module
            else:
                keep = len(package_parts) - (node.level - 1)
                prefix = package_parts[: max(keep, 0)]
                suffix = node.module.split(".") if node.module else []
                imported = ".".join([*prefix, *suffix])
            if imported:
                yield imported, tuple(alias.name for alias in node.names), node.lineno


def _source_location(path: Path, source_root: Path) -> tuple[str | None, str | None]:
    relative = path.relative_to(source_root).with_suffix("")
    parts = relative.parts
    if len(parts) < 4 or parts[0:2] != ("apistra", "modules"):
        return None, None
    module_name = parts[2]
    layer = (
        parts[3] if len(parts) > 3 and parts[3] in LAYER_ALLOWED_DEPENDENCIES else None
    )
    return module_name, layer


def _module_directories(modules_root: Path) -> list[Path]:
    if not modules_root.is_dir():
        return []
    return sorted(
        directory
        for directory in modules_root.iterdir()
        if directory.is_dir() and not directory.name.startswith("_")
    )


def _validate_module_shape(module_directories: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for module_directory in module_directories:
        if not (module_directory / "public.py").is_file():
            violations.append(
                Violation(
                    "ARCH-PUBLIC",
                    module_directory,
                    1,
                    "business module has no public.py contract",
                )
            )
        for layer in LAYER_ALLOWED_DEPENDENCIES:
            if not (module_directory / layer).is_dir():
                violations.append(
                    Violation(
                        "ARCH-MODULE-SHAPE",
                        module_directory,
                        1,
                        f"business module is missing its {layer!r} layer directory",
                    )
                )
    return violations


def _is_composition_root(path: Path, source_root: Path) -> bool:
    relative = path.relative_to(source_root)
    return (
        len(relative.parts) >= 4
        and relative.parts[0:2] == ("apistra", "entrypoints")
        and path.name == "composition.py"
    )


def _check_module_import(
    *,
    imported: str,
    imported_names: tuple[str, ...],
    path: Path,
    line: int,
    source_module: str | None,
    source_layer: str | None,
    is_composition_root: bool,
    module_graph: dict[str, set[str]],
) -> list[Violation]:
    target_parts = imported.split(".")
    if len(target_parts) < 3 or target_parts[0:2] != ["apistra", "modules"]:
        return []
    violations: list[Violation] = []
    target_module = target_parts[2]
    if source_module and target_module != source_module:
        module_graph.setdefault(source_module, set()).add(target_module)
        public_path = target_parts[3:] == ["public"]
        public_from_package = target_parts[3:] == [] and imported_names == ("public",)
        if not (public_path or public_from_package):
            violations.append(
                Violation(
                    "ARCH-MODULE-PUBLIC",
                    path,
                    line,
                    f"cross-module import must use apistra.modules.{target_module}.public",
                )
            )
    if source_module == target_module and source_layer and len(target_parts) >= 4:
        target_layer = target_parts[3]
        if (
            target_layer in LAYER_ALLOWED_DEPENDENCIES
            and target_layer not in LAYER_ALLOWED_DEPENDENCIES[source_layer]
        ):
            violations.append(
                Violation(
                    "ARCH-LAYERS",
                    path,
                    line,
                    f"{source_layer} may not import outward layer {target_layer}",
                )
            )
    if len(target_parts) >= 4 and target_parts[3] == "adapters":
        outside_own_module = source_module != target_module
        if outside_own_module and not is_composition_root:
            violations.append(
                Violation(
                    "ARCH-011",
                    path,
                    line,
                    "concrete adapters may only be imported by an entrypoint composition root",
                )
            )
    return violations


def _check_import(
    *,
    imported: str,
    imported_names: tuple[str, ...],
    path: Path,
    line: int,
    source_module: str | None,
    source_layer: str | None,
    composition_root: bool,
    module_graph: dict[str, set[str]],
) -> list[Violation]:
    violations: list[Violation] = []
    if source_layer == "domain" and imported.startswith(DOMAIN_FORBIDDEN_PREFIXES):
        violations.append(
            Violation(
                "ARCH-001", path, line, f"domain imports outer dependency {imported!r}"
            )
        )
    violations.extend(
        _check_module_import(
            imported=imported,
            imported_names=imported_names,
            path=path,
            line=line,
            source_module=source_module,
            source_layer=source_layer,
            is_composition_root=composition_root,
            module_graph=module_graph,
        )
    )
    if imported.startswith(("engineering", "softwaretest")):
        violations.append(
            Violation(
                "ARCH-010",
                path,
                line,
                "engineering integrations must remain outside the product runtime graph",
            )
        )
    return violations


def _analyse_file(
    path: Path, source_root: Path, module_graph: dict[str, set[str]]
) -> list[Violation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        return [Violation("ARCH-SYNTAX", path, error.lineno or 1, error.msg)]
    source_module, source_layer = _source_location(path, source_root)
    composition_root = _is_composition_root(path, source_root)
    violations: list[Violation] = []
    for imported, imported_names, line in _imports(tree, path, source_root):
        violations.extend(
            _check_import(
                imported=imported,
                imported_names=imported_names,
                path=path,
                line=line,
                source_module=source_module,
                source_layer=source_layer,
                composition_root=composition_root,
                module_graph=module_graph,
            )
        )
    return violations


def _cycle_violations(
    modules_root: Path, module_graph: dict[str, set[str]]
) -> list[Violation]:
    violations: list[Violation] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(module_name: str) -> None:
        if module_name in active:
            cycle = active[active.index(module_name) :] + [module_name]
            violations.append(
                Violation(
                    "ARCH-013",
                    modules_root,
                    1,
                    f"cyclic business-module dependency: {' -> '.join(cycle)}",
                )
            )
            return
        if module_name in visited:
            return
        active.append(module_name)
        for dependency in sorted(module_graph.get(module_name, set())):
            if dependency in module_graph:
                visit(dependency)
        active.pop()
        visited.add(module_name)

    for module_name in sorted(module_graph):
        visit(module_name)
    return violations


def analyse_source_root(source_root: Path) -> list[Violation]:
    source_root = source_root.resolve()
    python_files = sorted(source_root.rglob("*.py"))
    if not python_files:
        return [
            Violation(
                "ARCH-SCOPE",
                source_root,
                1,
                "architecture scope contains no Python files",
            )
        ]
    modules_root = source_root / "apistra" / "modules"
    module_directories = _module_directories(modules_root)
    if not module_directories:
        return [
            Violation("ARCH-SCOPE", modules_root, 1, "no business module is present")
        ]
    module_graph = {directory.name: set() for directory in module_directories}
    violations = _validate_module_shape(module_directories)

    for path in python_files:
        violations.extend(_analyse_file(path, source_root, module_graph))
    violations.extend(_cycle_violations(modules_root, module_graph))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Apistra Python architecture rules."
    )
    parser.add_argument("source_root", type=Path)
    args = parser.parse_args()
    violations = analyse_source_root(args.source_root)
    for violation in violations:
        print(violation.render())
    if violations:
        print(f"Architecture check failed with {len(violations)} violation(s).")
        return 1
    print("Python architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
