from pathlib import Path

OUTPUT_FILE = "sapientia_codebase.txt"

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".next",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    ".DS_Store",
}

INCLUDED_EXTENSIONS = {
    ".py",
    ".sql",
    ".tsx",
    ".ts",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
    ".css",
    ".scss",
    ".html",
}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def export_codebase(root: Path):
    files = []

    for file in sorted(root.rglob("*")):

        if not file.is_file():
            continue

        if should_skip(file):
            continue

        if file.suffix.lower() not in INCLUDED_EXTENSIONS:
            continue

        files.append(file)

    print(f"Found {len(files)} files")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        out.write("=" * 120 + "\n")
        out.write("SAPIENTIA CODEBASE EXPORT\n")
        out.write("=" * 120 + "\n\n")

        for file in files:

            relative = file.relative_to(root)

            print(relative)

            out.write("\n")
            out.write("=" * 120 + "\n")
            out.write(f"FILE: {relative}\n")
            out.write("=" * 120 + "\n\n")

            try:
                text = file.read_text(encoding="utf-8")

            except UnicodeDecodeError:
                try:
                    text = file.read_text(encoding="latin1")
                except Exception:
                    text = "<< Unable to decode file >>"

            out.write(text)
            out.write("\n\n")

    print(f"\nExport written to {OUTPUT_FILE}")


if __name__ == "__main__":

    project_root = Path(".").resolve()

    export_codebase(project_root)