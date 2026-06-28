"""
Module: main.py

Purpose:
Sapientia command-line entry point.
"""

import argparse

from sapientia.cli.ingest_cli import run_ingest
from sapientia.cli.semantic_cli import run_semantic
from sapientia.cli.knowledge_cli import run_knowledge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sapientia CLI")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest metadata from a source and optionally run semantic analysis",
    )
    ingest_parser.add_argument("--project-id", type=int, required=True)
    ingest_parser.add_argument("--file-path", type=str, required=True)
    ingest_parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["csv", "json"],
    )
    ingest_parser.add_argument(
        "--run-semantic",
        action="store_true",
        help="Run semantic analysis after ingestion completes",
    )

    semantic_parser = subparsers.add_parser(
        "semantic",
        help="Run semantic analysis for a dataset",
    )
    semantic_parser.add_argument("--dataset-id", type=int, required=True)

    knowledge_parser = subparsers.add_parser(
        "knowledge",
        help="Acquire enterprise knowledge from a local document",
    )
    knowledge_parser.add_argument("--project-id", type=int, required=True)
    knowledge_parser.add_argument("--file-path", type=str, required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        result = run_ingest(args)

    elif args.command == "semantic":
        result = run_semantic(args)

    elif args.command == "knowledge":
        result = run_knowledge(args)

    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print("Execution completed.")
    print(result)


if __name__ == "__main__":
    main()