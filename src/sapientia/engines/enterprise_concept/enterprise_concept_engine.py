"""
Module: enterprise_concept_engine.py

Purpose:
Consolidates semantic classifications, enterprise knowledge and fusion
links into persistent enterprise concepts.
"""

from collections import defaultdict

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.enterprise_concept_repository import (
    EnterpriseConceptRepository,
)


class EnterpriseConceptEngine:
    CONCEPT_RULES = {
        "INVOICE": {
            "concept_name": "Invoice",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["invoice", "inv_"],
        },
        "CUSTOMER": {
            "concept_name": "Customer",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["customer", "cust_"],
        },
        "PAYMENT": {
            "concept_name": "Payment",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["payment", "paid", "overdue"],
        },
        "REVENUE": {
            "concept_name": "Revenue",
            "concept_type": "BUSINESS_MEASURE",
            "keywords": ["revenue", "total_amount", "invoice_amount"],
        },
        "TAX": {
            "concept_name": "Tax",
            "concept_type": "BUSINESS_MEASURE",
            "keywords": ["tax", "gst"],
        },
        "GENERAL_LEDGER": {
            "concept_name": "General Ledger",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["gl_", "ledger", "account_code"],
        },
        "SUPPLIER": {
            "concept_name": "Supplier",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["supplier", "vendor"],
        },
        "PURCHASE_ORDER": {
            "concept_name": "Purchase Order",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["purchase_order", "po_"],
        },
        "ORDER": {
            "concept_name": "Order",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["order_id", "orders", "order_line"],
        },
        "PRODUCT": {
            "concept_name": "Product",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["product", "item"],
        },
        "EMPLOYEE": {
            "concept_name": "Employee",
            "concept_type": "BUSINESS_ENTITY",
            "keywords": ["employee", "payroll"],
        },
    }

    def build_domain_concepts(
        self,
        project_id: int,
        business_domain: str,
        refresh: bool = True,
    ) -> dict:
        business_domain = business_domain.upper()
        engine = get_engine()

        with engine.begin() as connection:
            repository = EnterpriseConceptRepository(connection)

            domain = repository.get_business_domain(business_domain)
            business_domain_id = domain.get("business_domain_id")

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

            concepts = self._derive_concepts(
                semantic_columns=semantic_columns,
                knowledge_items=knowledge_items,
                intelligence_links=intelligence_links,
            )

            if refresh:
                repository.delete_existing_concepts(
                    project_id=project_id,
                    business_domain_id=business_domain_id,
                )

            persisted = []

            for concept in concepts:
                concept_id = repository.create_concept(
                    project_id=project_id,
                    business_domain_id=business_domain_id,
                    concept=concept,
                )

                for evidence in concept.get("evidence", []):
                    repository.create_evidence(
                        enterprise_concept_id=concept_id,
                        evidence=evidence,
                    )

                persisted.append(
                    {
                        "enterprise_concept_id": concept_id,
                        "concept_name": concept["concept_name"],
                        "concept_type": concept["concept_type"],
                        "confidence_score": concept["confidence_score"],
                        "evidence_count": len(concept.get("evidence", [])),
                    }
                )

        return {
            "project_id": project_id,
            "business_domain": business_domain,
            "concepts_created": len(persisted),
            "concepts": persisted,
        }

    def _derive_concepts(
        self,
        semantic_columns: list[dict],
        knowledge_items: list[dict],
        intelligence_links: list[dict],
    ) -> list[dict]:
        concept_evidence = defaultdict(list)

        for column in semantic_columns:
            text_blob = " ".join(
                [
                    str(column.get("dataset_name", "")),
                    str(column.get("column_name", "")),
                    str(column.get("semantic_type", "")),
                    str(column.get("business_meaning", "")),
                ]
            ).lower()

            for rule_code, rule in self.CONCEPT_RULES.items():
                if self._matches_any(text_blob, rule["keywords"]):
                    concept_evidence[rule_code].append(
                        {
                            "evidence_type": "SEMANTIC",
                            "evidence_source": "Semantic Engine",
                            "evidence_text": (
                                f"{column.get('dataset_name')}."
                                f"{column.get('column_name')} was classified as "
                                f"{column.get('semantic_type')}."
                            ),
                            "dataset_id": column.get("dataset_id"),
                            "column_id": column.get("column_id"),
                            "confidence_score": column.get("confidence_score"),
                        }
                    )

        for item in knowledge_items:
            text_blob = " ".join(
                [
                    str(item.get("name", "")),
                    str(item.get("description", "")),
                    str(item.get("knowledge_type", "")),
                ]
            ).lower()

            for rule_code, rule in self.CONCEPT_RULES.items():
                if self._matches_any(text_blob, rule["keywords"]):
                    concept_evidence[rule_code].append(
                        {
                            "evidence_type": "KNOWLEDGE",
                            "evidence_source": "Knowledge Acquisition Engine",
                            "evidence_text": (
                                f"Knowledge item '{item.get('name')}' supports "
                                f"the concept {rule['concept_name']}."
                            ),
                            "knowledge_item_id": item.get("knowledge_item_id"),
                            "confidence_score": None,
                        }
                    )

        for link in intelligence_links:
            text_blob = " ".join(
                [
                    str(link.get("dataset_name", "")),
                    str(link.get("column_name", "")),
                    str(link.get("semantic_type", "")),
                    str(link.get("business_meaning", "")),
                    str(link.get("knowledge_name", "")),
                    str(link.get("knowledge_description", "")),
                ]
            ).lower()

            for rule_code, rule in self.CONCEPT_RULES.items():
                if self._matches_any(text_blob, rule["keywords"]):
                    concept_evidence[rule_code].append(
                        {
                            "evidence_type": "FUSION",
                            "evidence_source": "Knowledge Fusion Engine",
                            "evidence_text": (
                                f"Fusion linked {link.get('dataset_name')}."
                                f"{link.get('column_name')} to "
                                f"'{link.get('knowledge_name')}'."
                            ),
                            "dataset_id": link.get("dataset_id"),
                            "column_id": link.get("column_id"),
                            "knowledge_item_id": link.get("knowledge_item_id"),
                            "intelligence_link_id": link.get("intelligence_link_id"),
                            "confidence_score": link.get("fusion_confidence_score"),
                        }
                    )

        concepts = []

        for rule_code, evidence in concept_evidence.items():
            rule = self.CONCEPT_RULES[rule_code]
            confidence = self._calculate_confidence(evidence)

            concepts.append(
                {
                    "concept_code": rule_code,
                    "concept_name": rule["concept_name"],
                    "concept_type": rule["concept_type"],
                    "concept_description": self._build_description(
                        concept_name=rule["concept_name"],
                        concept_type=rule["concept_type"],
                        evidence_count=len(evidence),
                    ),
                    "confidence_score": confidence,
                    "evidence_count": len(evidence),
                    "evidence": evidence,
                }
            )

        concepts.sort(
            key=lambda concept: (
                concept["concept_type"],
                concept["concept_name"],
            )
        )

        return concepts

    def _matches_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword.lower() in text for keyword in keywords)

    def _calculate_confidence(self, evidence: list[dict]) -> float:
        scores = [
            float(item["confidence_score"])
            for item in evidence
            if item.get("confidence_score") is not None
        ]

        if not scores:
            return min(100.0, 50.0 + len(evidence) * 5)

        average = sum(scores) / len(scores)
        evidence_boost = min(10.0, len(evidence) * 1.5)

        return round(min(100.0, average + evidence_boost), 4)

    def _build_description(
        self,
        concept_name: str,
        concept_type: str,
        evidence_count: int,
    ) -> str:
        return (
            f"Sapientia identified {concept_name} as a {concept_type.lower()} "
            f"based on {evidence_count} evidence record(s) from semantic, "
            f"knowledge and fusion outputs."
        )