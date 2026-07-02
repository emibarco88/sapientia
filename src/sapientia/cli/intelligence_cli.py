"""
Module: intelligence_cli.py

Purpose:
CLI handler for Enterprise Intelligence reports.
"""

import json

from sapientia.services.enterprise_intelligence_service import (
    EnterpriseIntelligenceService,
)


def run_intelligence(args) -> dict:
    service = EnterpriseIntelligenceService()

    report = service.generate_domain_report(
        project_id=args.project_id,
        business_domain=args.business_domain,
        persist=not args.no_persist,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, default=str))

    elif args.format == "text":
        _print_text_report(report)

    else:
        raise ValueError(f"Unsupported report format: {args.format}")

    return {
        "intelligence_report_id": report.get("intelligence_report_id"),
        "report_type": report["report_type"],
        "project_id": report["project_id"],
        "business_domain": report["business_domain"],
        "datasets": len(report["datasets"]),
        "knowledge_items": len(report["knowledge_items"]),
        "intelligence_links": len(report["intelligence_links"]),
        "enterprise_concepts": len(report.get("enterprise_concepts", [])),
        "findings": len(report["findings"]),
    }


def _print_text_report(report: dict) -> None:
    summary = report.get("summary", {})

    print("\n")
    print("=" * 80)
    print("ENTERPRISE INTELLIGENCE REPORT")
    print("=" * 80)
    print(f"Report ID:       {report.get('intelligence_report_id')}")
    print(f"Project ID:      {report['project_id']}")
    print(f"Business Domain: {report['business_domain']}")
    print(f"Generated At:    {report['generated_at']}")
    print("-" * 80)

    print("\nSUMMARY")
    print(f"Datasets:             {summary.get('dataset_count', 0)}")
    print(f"Columns:              {summary.get('column_count', 0)}")
    print(f"Semantic Columns:     {summary.get('semantic_column_count', 0)}")
    print(f"Intelligence Links:   {summary.get('intelligence_link_count', 0)}")
    print(f"Enterprise Concepts:  {len(report.get('enterprise_concepts', []))}")

    print("\nSUMMARY TEXT")
    print(report.get("summary_text"))

    print("\nENTERPRISE CONCEPTS")
    for concept in report.get("enterprise_concepts", []):
        print(
            f"- [{concept.get('enterprise_concept_id')}] "
            f"{concept.get('concept_name')} "
            f"({concept.get('concept_type')}) "
            f"confidence={concept.get('confidence_score')} "
            f"evidence={concept.get('evidence_count')}"
        )

    print("\nFINDINGS")
    for finding in report.get("findings", [])[:20]:
        print(f"- [{finding.get('finding_type')}] {finding.get('finding_title')}")
        print(f"  {finding.get('finding_description')}")
        if finding.get("finding_interpretation"):
            print(f"  Why it matters: {finding.get('finding_interpretation')}")

    print("\nDATASETS")
    for dataset in report.get("datasets", []):
        print(
            f"- [{dataset['dataset_id']}] {dataset['name']} "
            f"({dataset['source_type']}, {dataset['object_type']})"
        )

    print("\nTOP INTELLIGENCE LINKS")
    for link in report.get("intelligence_links", [])[:15]:
        print(
            f"- {link.get('dataset_name')}.{link.get('column_name')} "
            f"→ {link.get('knowledge_name')} "
            f"({link.get('fusion_confidence_score')})"
        )

    print("\n")