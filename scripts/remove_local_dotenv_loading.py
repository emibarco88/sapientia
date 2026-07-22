from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/sapientia")
EXCLUDED_FILES = {
    Path("src/sapientia/config/environment.py"),
}


def should_remove_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return (
            node.module == "dotenv"
            and any(alias.name == "load_dotenv" for alias in node.names)
        )

    if isinstance(node, ast.Import):
        return any(alias.name == "dotenv" for alias in node.names)

    return False


def should_remove_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr):
        return False

    call = node.value

    if not isinstance(call, ast.Call):
        return False

    if isinstance(call.func, ast.Name):
        return call.func.id == "load_dotenv"

    if isinstance(call.func, ast.Attribute):
        return (
            isinstance(call.func.value, ast.Name)
            and call.func.value.id == "dotenv"
            and call.func.attr == "load_dotenv"
        )

    return False


def line_ranges_to_remove(tree: ast.AST) -> set[int]:
    lines: set[int] = set()

    for node in ast.walk(tree):
        if should_remove_import(node) or should_remove_call(node):
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", start)

            if start is not None and end is not None:
                lines.update(range(start, end + 1))

    return lines


def clean_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"SKIPPED syntax error: {path}: {exc}")
        return False

    lines_to_remove = line_ranges_to_remove(tree)

    if not lines_to_remove:
        return False

    original_lines = source.splitlines(keepends=True)

    cleaned_lines = [
        line
        for line_number, line in enumerate(original_lines, start=1)
        if line_number not in lines_to_remove
    ]

    cleaned = "".join(cleaned_lines)

    # Avoid excessive blank lines left by removed statements.
    while "\n\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n\n", "\n\n\n")

    path.write_text(cleaned, encoding="utf-8")
    return True


def main() -> None:
    changed_files: list[Path] = []

    for path in ROOT.rglob("*.py"):
        if path in EXCLUDED_FILES:
            continue

        if clean_file(path):
            changed_files.append(path)

    print()
    print(f"Updated {len(changed_files)} files:")

    for path in changed_files:
        print(f"  {path}")


if __name__ == "__main__":
    main()
