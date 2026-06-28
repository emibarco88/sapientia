"""
Module: main.py

Purpose:
Sapientia command-line entry point.
"""

import argparse

from sapientia.cli.ingest_cli import run_ingest
from sapientia.cli.profile_cli import run_profile
from sapientia.cli.semantic_cli import run_semantic
from sapientia.cli.knowledge_cli import run_knowledge
from sapientia.cli.fusion_cli import run_fusion


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sapientia CLI")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest metadata from a source",
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
        "--skip-profiling",
        action="store_true",
        help="Skip profiling during ingestion",
    )
    ingest_parser.add_argument(
        "--run-semantic",
        action="store_true",
        help="Run semantic analysis after ingestion completes",
    )

    profile_parser = subparsers.add_parser(
        "profile",
        help="Run profiling for an existing dataset",
    )
    profile_parser.add_argument("--dataset-id", type=int, required=True)

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

    fusion_parser = subparsers.add_parser(
        "fusion",
        help="Fuse enterprise knowledge with EKR data assets",
    )
    fusion_parser.add_argument("--project-id", type=int, required=True)
    fusion_parser.add_argument("--document-id", type=int, required=False)
    fusion_parser.add_argument("--dataset-id", type=int, required=False)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        result = run_ingest(args)

    elif args.command == "profile":
        result = run_profile(args)

    elif args.command == "semantic":
        result = run_semantic(args)

    elif args.command == "knowledge":
        result = run_knowledge(args)

    elif args.command == "fusion":
        result = run_fusion(args)

    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print("Execution completed.")
    print(result)


if __name__ == "__main__":
    main()