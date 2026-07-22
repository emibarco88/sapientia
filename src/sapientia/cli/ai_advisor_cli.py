"""
Module: ai_advisor_cli.py

Purpose:
CLI handler for Sapientia AI Advisor.
"""

from __future__ import annotations

from typing import Any

from sapientia.services.ai_advisor_service import (
    AIAdvisorService,
)


def run_ai_advisor(
    args: Any,
) -> dict[str, Any]:
    service = AIAdvisorService()

    result = service.ask_domain_question(
        project_id=args.project_id,
        business_domain=args.business_domain,
        question=args.question,
        persist=not args.no_persist,
    )

    print("\n")
    print("=" * 80)
    print("SAPIENTIA AI ADVISOR")
    print("=" * 80)

    print(
        f"Response ID:       "
        f"{result.get('ai_advisor_response_id')}"
    )

    print(
        f"Provider ID:       "
        f"{result.get('response_id')}"
    )

    print(
        f"Project ID:        "
        f"{result['project_id']}"
    )

    print(
        f"Business Domain:   "
        f"{result['business_domain']}"
    )

    print(
        f"Report ID:         "
        f"{result.get('intelligence_report_id')}"
    )

    print(
        f"Provider:          "
        f"{result.get('provider')}"
    )

    print(
        f"Model:             "
        f"{result.get('model')}"
    )

    print(
        f"Execution Time:    "
        f"{result.get('execution_time_ms')} ms"
    )

    print(
        f"Input Tokens:      "
        f"{result.get('input_tokens')}"
    )

    print(
        f"Output Tokens:     "
        f"{result.get('output_tokens')}"
    )

    print(
        f"Total Tokens:      "
        f"{result.get('total_tokens')}"
    )

    print(
        f"Retrieval Mode:    "
        f"{result.get('retrieval_mode')}"
    )

    print(
        f"Keywords:          "
        f"{result.get('keywords')}"
    )

    print(
        f"Fallback Used:     "
        f"{result.get('fallback_used')}"
    )

    print(
        f"Concepts Used:     "
        f"{result.get('concepts_used')}"
    )

    print(
        f"Findings Used:     "
        f"{result.get('findings_used')}"
    )

    print(
        f"Knowledge Used:    "
        f"{result.get('knowledge_items_used')}"
    )

    print(
        f"Asset Links Used:  "
        f"{result.get('knowledge_asset_links_used')}"
    )

    print(
        f"Document Chunks:   "
        f"{result.get('document_chunks_used')}"
    )

    warnings = (
        result.get("warnings")
        or []
    )

    if warnings:
        print(
            f"Warnings:          "
            f"{warnings}"
        )

    context_warning = result.get(
        "context_warning"
    )

    if context_warning:
        print(
            f"Context Warning:   "
            f"{context_warning}"
        )

    print("-" * 80)

    print("\nQUESTION")
    print(
        result["question"]
    )

    print("\nANSWER")
    print(
        result["answer"]
    )

    print("\n")

    return result