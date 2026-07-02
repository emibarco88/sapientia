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
from sapientia.cli.intelligence_cli import run_intelligence
from sapientia.cli.concept_cli import run_concepts
from sapientia.cli.ai_advisor_cli import run_ai_advisor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sapientia CLI")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Discover Enterprise Assets from a source",
    )
    ingest_parser.add_argument("--project-id", type=int, required=True)
    ingest_parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["csv", "json", "snowflake"],
    )
    ingest_parser.add_argument("--file-path", type=str, required=False)
    ingest_parser.add_argument("--business-domain", type=str, required=False, default="UNKNOWN")
    ingest_parser.add_argument("--skip-profiling", action="store_true")
    ingest_parser.add_argument("--run-semantic", action="store_true")
    ingest_parser.add_argument("--snowflake-database", type=str, required=False)
    ingest_parser.add_argument("--snowflake-schema", type=str, required=False)
    ingest_parser.add_argument("--snowflake-table", type=str, required=False)
    ingest_parser.add_argument("--table-limit", type=int, required=False, default=20)

    profile_parser = subparsers.add_parser(
        "profile",
        help="Run Enterprise Profiling for an existing dataset",
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
    knowledge_parser.add_argument("--business-domain", type=str, required=False, default="UNKNOWN")

    fusion_parser = subparsers.add_parser(
        "fusion",
        help="Fuse enterprise knowledge with EKR data assets",
    )
    fusion_parser.add_argument("--project-id", type=int, required=True)
    fusion_parser.add_argument("--document-id", type=int, required=False)
    fusion_parser.add_argument("--dataset-id", type=int, required=False)

    concepts_parser = subparsers.add_parser(
        "concepts",
        help="Build Enterprise Concepts from semantic, knowledge and fusion outputs",
    )
    concepts_parser.add_argument("--project-id", type=int, required=True)
    concepts_parser.add_argument("--business-domain", type=str, required=True)
    concepts_parser.add_argument("--no-refresh", action="store_true")

    intelligence_parser = subparsers.add_parser(
        "intelligence",
        help="Generate and persist Enterprise Intelligence reports",
    )
    intelligence_parser.add_argument("--project-id", type=int, required=True)
    intelligence_parser.add_argument("--business-domain", type=str, required=True)
    intelligence_parser.add_argument(
        "--format",
        type=str,
        required=False,
        default="text",
        choices=["text", "json"],
    )
    intelligence_parser.add_argument("--no-persist", action="store_true")

    ai_advisor_parser = subparsers.add_parser(
        "ai-advisor",
        help="Ask questions using Sapientia Enterprise Intelligence context",
    )
    ai_advisor_parser.add_argument("--project-id", type=int, required=True)
    ai_advisor_parser.add_argument("--business-domain", type=str, required=True)
    ai_advisor_parser.add_argument("--question", type=str, required=True)
    ai_advisor_parser.add_argument("--no-persist", action="store_true")

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
    elif args.command == "concepts":
        result = run_concepts(args)
    elif args.command == "intelligence":
        result = run_intelligence(args)
    elif args.command == "ai-advisor":
        result = run_ai_advisor(args)
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print("Execution completed.")
    print(result)


if __name__ == "__main__":
    main()