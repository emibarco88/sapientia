"""
Module: enterprise_intelligence_engine.py

Purpose:
Builds and persists deterministic Enterprise Intelligence from the EKR.
"""

from datetime import datetime, UTC

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.enterprise_intelligence_repository import (
    EnterpriseIntelligenceRepository,
)


class EnterpriseIntelligenceEngine:
    def generate_domain_report(
        self,
        project_id: int,
        business_domain: str,
        persist: bool = True,
    ) -> dict:
        business_domain = business_domain.upper()
        engine = get_engine()

        with engine.begin() as connection:
            repository = EnterpriseIntelligenceRepository(connection)

            domain = repository.get_business_domain(business_domain)

            domain_summary = repository.get_domain_summary(
                project_id=project_id,
                business_domain=business_domain,
            )

            datasets = repository.get_datasets(project_id, business_domain)
            semantic_columns = repository.get_semantic_columns(project_id, business_domain)
            knowledge_items = repository.get_knowledge_items(project_id, business_domain)
            intelligence_links = repository.get_intelligence_links(project_id, business_domain)
            lineage = repository.get_lineage(project_id, business_domain)

            findings = self._build_findings(
                project_id=project_id,
                business_domain_id=domain.get("business_domain_id"),
                datasets=datasets,
                semantic_columns=semantic_columns,
                knowledge_items=knowledge_items,
                intelligence_links=intelligence_links,
                lineage=lineage,
            )

            ai_context = self._build_ai_context(
                business_domain=business_domain,
                summary=domain_summary,
                datasets=datasets,
                semantic_columns=semantic_columns,
                knowledge_items=knowledge_items,
                intelligence_links=intelligence_links,
                lineage=lineage,
                findings=findings,
            )

            summary_text = self._build_summary_text(
                business_domain=business_domain,
                datasets=datasets,
                semantic_columns=semantic_columns,
                knowledge_items=knowledge_items,
                intelligence_links=intelligence_links,
                lineage=lineage,
            )

            report = {
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
                "findings": findings,
                "summary_text": summary_text,
                "ai_context": ai_context,
            }

            intelligence_report_id = None

            if persist:
                intelligence_report_id = repository.create_report(
                    project_id=project_id,
                    business_domain_id=domain.get("business_domain_id"),
                    report_scope="DOMAIN",
                    report_type="ENTERPRISE_INTELLIGENCE_DOMAIN_REPORT",
                    report_title=f"{business_domain} Enterprise Intelligence Report",
                    summary_text=summary_text,
                    report_json=report,
                    ai_context_json=ai_context,
                )

                for finding in findings:
                    finding_id = repository.create_finding(
                        intelligence_report_id=intelligence_report_id,
                        project_id=project_id,
                        business_domain_id=domain.get("business_domain_id"),
                        finding=finding,
                    )

                    for evidence in finding.get("evidence", []):
                        repository.create_evidence(
                            intelligence_finding_id=finding_id,
                            evidence=evidence,
                        )

            report["intelligence_report_id"] = intelligence_report_id

        return report

    def _build_summary_text(
        self,
        business_domain: str,
        datasets: list[dict],
        semantic_columns: list[dict],
        knowledge_items: list[dict],
        intelligence_links: list[dict],
        lineage: list[dict],
    ) -> str:
        return (
            f"Sapientia analysed the {business_domain} business domain. "
            f"It found {len(datasets)} enterprise dataset(s), "
            f"{len(semantic_columns)} semantic classification(s), "
            f"{len(knowledge_items)} knowledge item(s), "
            f"{len(intelligence_links)} intelligence link(s), and "
            f"{len(lineage)} lineage evidence record(s)."
        )

    def _build_findings(
        self,
        project_id: int,
        business_domain_id: int | None,
        datasets: list[dict],
        semantic_columns: list[dict],
        knowledge_items: list[dict],
        intelligence_links: list[dict],
        lineage: list[dict],
    ) -> list[dict]:
        findings = []

        findings.append(
            {
                "finding_type": "DOMAIN_SUMMARY",
                "finding_title": "Business domain intelligence summary",
                "finding_description": (
                    f"Sapientia analysed {len(datasets)} dataset(s), "
                    f"{len(semantic_columns)} semantic column(s), "
                    f"{len(knowledge_items)} knowledge item(s), and "
                    f"{len(intelligence_links)} intelligence link(s)."
                ),
                "finding_interpretation": (
                    "This finding summarises the current level of enterprise "
                    "understanding Sapientia has built for this business domain."
                ),
                "confidence_score": None,
                "severity_level": "INFO",
                "source_object_type": "BUSINESS_DOMAIN",
                "source_object_id": business_domain_id,
                "evidence": [],
            }
        )

        for column in semantic_columns:
            if column.get("is_key_candidate"):
                findings.append(
                    {
                        "finding_type": "BUSINESS_KEY",
                        "finding_title": (
                            f"{column['column_name']} appears to be a business key"
                        ),
                        "finding_description": (
                            f"Sapientia identified {column['dataset_name']}."
                            f"{column['column_name']} as a key candidate."
                        ),
                        "finding_interpretation": (
                            "This column may represent an important identifier "
                            "used to connect business processes, records or entities."
                        ),
                        "confidence_score": column.get("confidence_score"),
                        "severity_level": "INFO",
                        "source_object_type": "COLUMN",
                        "source_object_id": column.get("column_id"),
                        "evidence": [
                            {
                                "evidence_type": "SEMANTIC",
                                "evidence_source": "Semantic Engine",
                                "evidence_text": (
                                    f"Semantic type: {column.get('semantic_type')}; "
                                    f"Business meaning: {column.get('business_meaning')}"
                                ),
                                "dataset_id": column.get("dataset_id"),
                                "column_id": column.get("column_id"),
                                "confidence_score": column.get("confidence_score"),
                            }
                        ],
                    }
                )

            if column.get("is_pii"):
                findings.append(
                    {
                        "finding_type": "PII",
                        "finding_title": (
                            f"{column['column_name']} may contain PII"
                        ),
                        "finding_description": (
                            f"Sapientia classified {column['dataset_name']}."
                            f"{column['column_name']} as potentially sensitive."
                        ),
                        "finding_interpretation": (
                            "This column may require governance, security review, "
                            "masking or access control."
                        ),
                        "confidence_score": column.get("confidence_score"),
                        "severity_level": "MEDIUM",
                        "source_object_type": "COLUMN",
                        "source_object_id": column.get("column_id"),
                        "evidence": [
                            {
                                "evidence_type": "SEMANTIC",
                                "evidence_source": "Semantic Engine",
                                "evidence_text": (
                                    f"Column marked as PII with semantic type "
                                    f"{column.get('semantic_type')}."
                                ),
                                "dataset_id": column.get("dataset_id"),
                                "column_id": column.get("column_id"),
                                "confidence_score": column.get("confidence_score"),
                            }
                        ],
                    }
                )

        for link in intelligence_links:
            findings.append(
                {
                    "finding_type": "FUSION_LINK",
                    "finding_title": (
                        f"{link.get('column_name')} is linked to "
                        f"{link.get('knowledge_name')}"
                    ),
                    "finding_description": (
                        f"Sapientia linked {link.get('dataset_name')}."
                        f"{link.get('column_name')} to the knowledge item "
                        f"'{link.get('knowledge_name')}'."
                    ),
                    "finding_interpretation": (
                        "This indicates that the enterprise asset is governed by, "
                        "explained by, or related to documented business knowledge."
                    ),
                    "confidence_score": link.get("fusion_confidence_score"),
                    "severity_level": "INFO",
                    "source_object_type": "INTELLIGENCE_LINK",
                    "source_object_id": link.get("intelligence_link_id"),
                    "evidence": [
                        {
                            "evidence_type": "FUSION",
                            "evidence_source": "Knowledge Fusion Engine",
                            "evidence_text": link.get("reasoning"),
                            "dataset_id": link.get("dataset_id"),
                            "column_id": link.get("column_id"),
                            "knowledge_item_id": link.get("knowledge_item_id"),
                            "intelligence_link_id": link.get("intelligence_link_id"),
                            "confidence_score": link.get("fusion_confidence_score"),
                        }
                    ],
                }
            )

        if lineage:
            findings.append(
                {
                    "finding_type": "LINEAGE",
                    "finding_title": "Lineage evidence was discovered",
                    "finding_description": (
                        f"Sapientia captured {len(lineage)} lineage evidence record(s)."
                    ),
                    "finding_interpretation": (
                        "Lineage evidence helps explain how enterprise assets are "
                        "created, populated or derived from upstream objects."
                    ),
                    "confidence_score": None,
                    "severity_level": "INFO",
                    "source_object_type": "LINEAGE",
                    "source_object_id": None,
                    "evidence": [
                        {
                            "evidence_type": "LINEAGE",
                            "evidence_source": item.get("source_type"),
                            "evidence_text": item.get("source_query"),
                            "dataset_id": item.get("dataset_id"),
                            "confidence_score": None,
                        }
                        for item in lineage[:20]
                    ],
                }
            )

        return findings

    def _build_ai_context(
        self,
        business_domain: str,
        summary: dict,
        datasets: list[dict],
        semantic_columns: list[dict],
        knowledge_items: list[dict],
        intelligence_links: list[dict],
        lineage: list[dict],
        findings: list[dict],
    ) -> dict:
        return {
            "instruction": (
                "Use only this Sapientia Enterprise Intelligence context. "
                "Do not invent facts. If information is missing, say it is unknown."
            ),
            "business_domain": business_domain,
            "summary": summary,
            "enterprise_assets": datasets,
            "semantic_understanding": semantic_columns,
            "enterprise_knowledge": knowledge_items,
            "intelligence_links": intelligence_links,
            "lineage": lineage,
            "findings": [
                {
                    "finding_type": finding.get("finding_type"),
                    "finding_title": finding.get("finding_title"),
                    "finding_description": finding.get("finding_description"),
                    "finding_interpretation": finding.get("finding_interpretation"),
                    "confidence_score": finding.get("confidence_score"),
                    "severity_level": finding.get("severity_level"),
                }
                for finding in findings
            ],
        }