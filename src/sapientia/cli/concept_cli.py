"""
Module: concept_cli.py

Purpose:
CLI handler for Enterprise Concept generation.
"""

from sapientia.services.enterprise_concept_service import EnterpriseConceptService


def run_concepts(args) -> dict:
    service = EnterpriseConceptService()

    result = service.build_domain_concepts(
        project_id=args.project_id,
        business_domain=args.business_domain,
        refresh=not args.no_refresh,
    )

    print("Enterprise concepts generated.")
    print(result)

    return result