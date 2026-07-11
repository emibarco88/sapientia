"""
Module: ai_advisor_cli.py

Purpose:
CLI handler for Sapientia AI Advisor.
"""

from sapientia.services.ai_advisor_service import AIAdvisorService


def run_ai_advisor(args) -> dict:
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
    print(f"Response ID:       {result.get('ai_advisor_response_id')}")
    print(f"Project ID:        {result['project_id']}")
    print(f"Business Domain:   {result['business_domain']}")
    print(f"Report ID:         {result['intelligence_report_id']}")
    print(f"Model:             {result['model']}")
    print(f"Retrieval Mode:    {result.get('retrieval_mode')}")
    print(f"Keywords:          {result.get('keywords')}")
    print(f"Fallback Used:     {result.get('fallback_used')}")
    print(f"Concepts Used:     {result.get('concepts_used')}")
    print(f"Findings Used:     {result.get('findings_used')}")
    print(f"Fusion Links Used: {result.get('fusion_links_used')}")
    print("-" * 80)

    print("\nQUESTION")
    print(result["question"])

    print("\nANSWER")
    print(result["answer"])
    print("\n")

    return result