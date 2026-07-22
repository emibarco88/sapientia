from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


DEFAULT_ROOT = Path("src/sapientia")

EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".next",
}

IMPORTANT_NAME_TERMS = {
    "ai_advisor",
    "advisor",
    "enterprise_ai",
    "context_retrieval",
    "prompt",
    "intelligence",
}

SEARCH_TERMS = {
    "SapientiaOpenAIClient",
    "EnterpriseAIEngine",
    "generate_answer",
    "answer_question",
    "AIAdvisor",
    "ai_advisor",
    "ContextRetrieval",
    "context_retrieval",
}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def read_text_safely(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError as exc:
        return f"[ERROR READING FILE: {exc}]"


def is_relevant_by_name(path: Path) -> bool:
    normalised = str(path).lower()
    return any(term in normalised for term in IMPORTANT_NAME_TERMS)


def is_relevant_by_content(content: str) -> bool:
    return any(term in content for term in SEARCH_TERMS)


def collect_relevant_files(root: Path) -> list[Path]:
    relevant: set[Path] = set()

    for path in root.rglob("*.py"):
        if is_excluded(path):
            continue

        content = read_text_safely(path)
        if content is None:
            continue

        if is_relevant_by_name(path) or is_relevant_by_content(content):
            relevant.add(path)

    return sorted(relevant)


def format_tree(paths: list[Path], project_root: Path) -> str:
    lines = ["Relevant file list:", ""]

    for path in paths:
        try:
            relative = path.relative_to(project_root)
        except ValueError:
            relative = path

        lines.append(f"- {relative}")

    return "\n".join(lines)


def format_file_section(path: Path, project_root: Path) -> str:
    try:
        relative = path.relative_to(project_root)
    except ValueError:
        relative = path

    content = read_text_safely(path)

    if content is None:
        content = "[BINARY OR NON-UTF-8 FILE SKIPPED]"

    return (
        "\n"
        + "=" * 100
        + "\n"
        + f"FILE: {relative}\n"
        + "=" * 100
        + "\n\n"
        + content.rstrip()
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Export Sapientia AI Advisor and Enterprise AI integration "
            "context into a single review file."
        )
    )
    parser.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help="Source root to scan. Default: src/sapientia",
    )
    parser.add_argument(
        "--output",
        default="sapientia_ai_advisor_migration_context.txt",
        help="Output file path.",
    )

    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    source_root = (project_root / args.root).resolve()
    output_path = (project_root / args.output).resolve()

    if not source_root.exists():
        raise FileNotFoundError(
            f"Source root does not exist: {source_root}"
        )

    relevant_files = collect_relevant_files(source_root)

    header = f"""Sapientia AI Advisor Migration Context
Generated: {datetime.now().isoformat(timespec="seconds")}
Project root: {project_root}
Source root: {source_root}
Files collected: {len(relevant_files)}

Purpose:
This export contains the current AI Advisor, Enterprise AI Engine,
context retrieval, service, API, CLI, prompt, and related integration code
needed to migrate the AI Advisor from SapientiaOpenAIClient to EnterpriseAIEngine.

"""

    sections = [
        header,
        format_tree(relevant_files, project_root),
        "\n",
    ]

    for path in relevant_files:
        sections.append(
            format_file_section(
                path=path,
                project_root=project_root,
            )
        )

    output_path.write_text(
        "".join(sections),
        encoding="utf-8",
    )

    print(f"Created: {output_path}")
    print(f"Files included: {len(relevant_files)}")

    if not relevant_files:
        print(
            "Warning: no relevant files were found. "
            "Check the --root path."
        )


if __name__ == "__main__":
    main()
