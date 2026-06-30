"""
Module: enterprise_intelligence_report_engine.py

Purpose:
Builds deterministic Enterprise Intelligence reports from the EKR.
"""

from datetime import datetime, UTC

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.enterprise_intelligence_repository import (
    EnterpriseIntelligenceRepository,
)


class EnterpriseIntelligenceReportEngine:
    def generate_domain_report(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict:
        business_domain = business_domain.upper()

        engine = get_engine()

        with engine.begin() as connection:
            repository = EnterpriseIntelligenceRepository(connection)

            domain_summary = repository.get_domain_summary(
                project_id=project_id,
                business_domain=business_domain,
            )

            datasets = repository.get_datasets(
                project_id=project_id,
                business_domain=business_domain,
            )

            semantic_columns = repository.get_semantic_columns(
                project_id=project_id,
                business_domain=business_domain,
            )

            knowledge_items = repository.get_knowledge_items(
                project_id=project_id,
                business_domain=business_domain,
            )

            intelligence_links = repository.get_intelligence_links(
                project_id=project_id,
                business_domain=business_domain,
            )

            lineage = repository.get_lineage(
                project_id=project_id,
                business_domain=business_domain,
            )

        return {
            "report_type": "ENTERPRISE_INTELLIGENCE_DOMAIN_REPORT",
            "generated_at": datetime.now(UTC).isoformat(),
            "project_id": project_id,
            "business_domain": business_domain,
            "summary": domain_summary,
            "datasets": datasets,
            "semantic_columns": semantic_columns,
            "knowledge_items": knowledge_items,
            "intelligence_links": intelligence_links,
            "lineage": lineage,
            "deterministic_findings": self._build_findings(
                datasets=datasets,
                semantic_columns=semantic_columns,
                knowledge_items=knowledge_items,
                intelligence_links=intelligence_links,
                lineage=lineage,
            ),
        }

    def _build_findings(
        self,
        datasets: list[dict],
        semantic_columns: list[dict],
        knowledge_items: list[dict],
        intelligence_links: list[dict],
        lineage: list[dict],
    ) -> list[str]:
        findings = []

        findings.append(
            f"Sapientia analysed {len(datasets)} enterprise dataset(s)."
        )

        findings.append(
            f"Sapientia identified {len(semantic_columns)} semantic column classification(s)."
        )

        findings.append(
            f"Sapientia acquired {len(knowledge_items)} knowledge item(s) from enterprise documents."
        )

        findings.append(
            f"Sapientia generated {len(intelligence_links)} intelligence link(s) between enterprise assets and knowledge."
        )

        if lineage:
            findings.append(
                f"Sapientia captured {len(lineage)} lineage evidence record(s)."
            )

        key_candidates = [
            column
            for column in semantic_columns
            if column.get("is_key_candidate")
        ]

        if key_candidates:
            key_names = sorted(
                {
                    f"{column['dataset_name']}.{column['column_name']}"
                    for column in key_candidates
                }
            )

            findings.append(
                "Potential business keys identified: "
                + ", ".join(key_names[:10])
            )

        pii_columns = [
            column
            for column in semantic_columns
            if column.get("is_pii")
        ]

        if pii_columns:
            pii_names = sorted(
                {
                    f"{column['dataset_name']}.{column['column_name']}"
                    for column in pii_columns
                }
            )

            findings.append(
                "Potential PII columns identified: "
                + ", ".join(pii_names[:10])
            )
        else:
            findings.append("No PII columns were identified by the current semantic rules.")

        return findings