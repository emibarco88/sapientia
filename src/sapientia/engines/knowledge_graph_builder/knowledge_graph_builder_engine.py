"""Deterministic business-level knowledge graph builder."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import re
from typing import Any

from sapientia.db.connection import get_engine
from sapientia.repositories.knowledge_graph_builder.knowledge_graph_builder_repository import (
    KnowledgeGraphBuilderRepository,
)


@dataclass(frozen=True)
class CandidateRule:
    key: str
    name: str
    object_type: str
    description: str
    patterns: tuple[str, ...]


RULES: tuple[CandidateRule, ...] = (
    CandidateRule("INVOICE", "Invoice", "BUSINESS_ENTITY", "A supplier or customer invoice representing a financial obligation.", (r"\bINVOICE\b", r"\bINV\b")),
    CandidateRule("PURCHASE_ORDER", "Purchase Order", "BUSINESS_ENTITY", "A purchase order authorising procurement of goods or services.", (r"\bPURCHASE[_ ]?ORDER\b", r"\bPO\b")),
    CandidateRule("GOODS_RECEIPT", "Goods Receipt", "BUSINESS_ENTITY", "Confirmation that ordered goods or services were received.", (r"\bGOODS[_ ]?RECEIPT\b", r"\bRECEIPT\b", r"\bRECEIVED\b")),
    CandidateRule("SUPPLIER", "Supplier", "BUSINESS_ENTITY", "An organisation supplying goods or services.", (r"\bSUPPLIER\b", r"\bVENDOR\b")),
    CandidateRule("CUSTOMER", "Customer", "BUSINESS_ENTITY", "A customer receiving products or services.", (r"\bCUSTOMER\b", r"\bCLIENT\b")),
    CandidateRule("COST_CENTRE", "Cost Centre", "BUSINESS_ENTITY", "An organisational unit to which financial activity is allocated.", (r"\bCOST[_ ]?CENT(?:ER|RE)\b",)),
    CandidateRule("CURRENCY", "Currency", "BUSINESS_CONCEPT", "The currency in which a transaction or amount is expressed.", (r"\bCURRENCY\b", r"\bCURRENCY[_ ]?CODE\b")),
    CandidateRule("PAYMENT", "Payment", "BUSINESS_ENTITY", "A settlement of a financial obligation.", (r"\bPAYMENT\b", r"\bPAID\b")),
    CandidateRule("GENERAL_LEDGER", "General Ledger", "BUSINESS_ENTITY", "The central accounting record for financial postings.", (r"\bGENERAL[_ ]?LEDGER\b", r"\bGL[_ ]?ACCOUNT\b", r"\bLEDGER\b")),
    CandidateRule("PRODUCT", "Product", "BUSINESS_ENTITY", "A product, material or service item involved in a transaction.", (r"\bPRODUCT\b", r"\bSKU\b", r"\bMATERIAL\b", r"\bITEM\b")),
    CandidateRule("REVENUE", "Revenue", "BUSINESS_METRIC", "Income recognised from business activity.", (r"\bREVENUE\b", r"\bSALES[_ ]?AMOUNT\b")),
    CandidateRule("TAX", "Tax", "BUSINESS_CONCEPT", "A tax amount or tax classification associated with a transaction.", (r"\bTAX\b", r"\bGST\b", r"\bVAT\b")),
    CandidateRule("FREIGHT", "Freight", "BUSINESS_CONCEPT", "Freight or delivery cost associated with a transaction.", (r"\bFREIGHT\b", r"\bSHIPPING\b")),
    CandidateRule("UNIT_PRICE", "Unit Price", "BUSINESS_METRIC", "The price applied to one unit of a product or service.", (r"\bUNIT[_ ]?PRICE\b",)),
    CandidateRule("QUANTITY", "Quantity", "BUSINESS_METRIC", "The number of units ordered, received or invoiced.", (r"\bQUANTITY\b", r"\bQTY\b")),
)

RELATIONSHIP_RULES: tuple[tuple[str, str, str, float, str], ...] = (
    ("PURCHASE_ORDER", "INVOICE", "MATCHED_TO", 0.94, "Purchase orders and invoices are compared during invoice matching."),
    ("GOODS_RECEIPT", "PURCHASE_ORDER", "CONFIRMS", 0.93, "A goods receipt confirms fulfilment of a purchase order."),
    ("INVOICE", "GOODS_RECEIPT", "MATCHED_TO", 0.92, "Invoices are matched to goods receipts during three-way matching."),
    ("INVOICE", "COST_CENTRE", "ALLOCATED_TO", 0.88, "Invoice costs are allocated to a cost centre."),
    ("PURCHASE_ORDER", "COST_CENTRE", "ALLOCATED_TO", 0.86, "Purchase order commitments are allocated to a cost centre."),
    ("INVOICE", "CURRENCY", "DENOMINATED_IN", 0.91, "Invoice amounts are denominated in a currency."),
    ("PURCHASE_ORDER", "CURRENCY", "DENOMINATED_IN", 0.89, "Purchase order amounts are denominated in a currency."),
    ("PAYMENT", "CURRENCY", "DENOMINATED_IN", 0.87, "Payments are denominated in a currency."),
    ("INVOICE", "TAX", "INCLUDES", 0.90, "An invoice can include tax."),
    ("PURCHASE_ORDER", "FREIGHT", "INCLUDES", 0.84, "A purchase order can include freight charges."),
    ("PRODUCT", "UNIT_PRICE", "PRICED_BY", 0.90, "A product or service line is priced using a unit price."),
    ("INVOICE", "QUANTITY", "MEASURED_BY", 0.84, "Invoice lines can be measured by quantity."),
    ("PURCHASE_ORDER", "QUANTITY", "MEASURED_BY", 0.84, "Purchase order lines can be measured by quantity."),
    ("SUPPLIER", "PURCHASE_ORDER", "RELATED_TO", 0.88, "Suppliers fulfil purchase orders."),
    ("SUPPLIER", "INVOICE", "RELATED_TO", 0.88, "Suppliers issue invoices."),
    ("CUSTOMER", "INVOICE", "RELATED_TO", 0.88, "Customers receive invoices."),
    ("INVOICE", "GENERAL_LEDGER", "PRODUCES", 0.86, "Approved invoices produce accounting postings."),
    ("PAYMENT", "INVOICE", "RELATED_TO", 0.88, "Payments settle invoice obligations."),
)


class KnowledgeGraphBuilderEngine:
    VERSION = "1.0"

    def build(self, project_id: int, business_domain: str) -> dict[str, Any]:
        if project_id <= 0:
            raise ValueError("project_id must be greater than zero.")
        domain = str(business_domain or "").strip().upper()
        if not domain:
            raise ValueError("A business domain is required.")

        engine = get_engine()
        run_id: int | None = None

        try:
            with engine.begin() as connection:
                repository = KnowledgeGraphBuilderRepository(connection)
                run_id = repository.create_run(project_id, domain)
                repository.set_stage(run_id, "LOADING_EVIDENCE")
                rows = repository.load_column_evidence(project_id, domain)
                repository.deactivate_generated_scope(project_id, domain)

                candidates = self._identify_candidates(rows)
                repository.set_stage(run_id, "BUILDING_BUSINESS_OBJECTS")

                object_ids: dict[str, int] = {}
                evidence_count = 0
                object_summaries: list[dict[str, Any]] = []

                for key, candidate in candidates.items():
                    rule: CandidateRule = candidate["rule"]
                    evidence_rows: list[dict[str, Any]] = candidate["evidence"]
                    confidence = self._candidate_confidence(evidence_rows)
                    canonical_key = f"business:{domain.lower()}:{key.lower()}"
                    object_id = repository.upsert_business_object(
                        project_id=project_id,
                        object_type_code=rule.object_type,
                        canonical_name=rule.name,
                        canonical_key=canonical_key,
                        source_object_id=self._stable_bigint(canonical_key),
                        description=rule.description,
                        business_domain=domain,
                        metadata={
                            "generated_by": "KNOWLEDGE_GRAPH_BUILDER",
                            "builder_version": self.VERSION,
                            "candidate_key": key,
                            "confidence": confidence,
                            "evidence_count": len(evidence_rows),
                            "datasets": sorted({str(row["dataset_name"]) for row in evidence_rows}),
                        },
                    )
                    object_ids[key] = object_id

                    for row in evidence_rows:
                        evidence_key = f"column:{row['column_id']}"
                        score = self._evidence_score(row)
                        repository.upsert_object_evidence(
                            business_object_id=object_id,
                            evidence_object_id=row.get("evidence_enterprise_object_id"),
                            source_record_id=int(row["column_id"]),
                            evidence_key=evidence_key,
                            score=score,
                            reasoning=self._evidence_reasoning(rule, row),
                            evidence={
                                "column_name": row["column_name"],
                                "dataset_id": row["dataset_id"],
                                "dataset_name": row["dataset_name"],
                                "source_system_name": row["source_system_name"],
                                "semantic_type": row.get("semantic_type"),
                                "business_meaning": row.get("business_meaning"),
                                "is_key_candidate": bool(row.get("is_key_candidate")),
                                "key_type": row.get("key_type"),
                            },
                            build_run_id=run_id,
                        )
                        evidence_count += 1

                    object_summaries.append({
                        "key": key,
                        "name": rule.name,
                        "object_type": rule.object_type,
                        "enterprise_object_id": object_id,
                        "confidence": confidence,
                        "evidence_count": len(evidence_rows),
                    })

                repository.set_stage(run_id, "INFERRING_RELATIONSHIPS")
                relationship_summaries: list[dict[str, Any]] = []

                for source_key, target_key, rel_type, base_confidence, reasoning in RELATIONSHIP_RULES:
                    if source_key not in object_ids or target_key not in object_ids:
                        continue
                    source_evidence = candidates[source_key]["evidence"]
                    target_evidence = candidates[target_key]["evidence"]
                    datasets_overlap = sorted(
                        {int(row["dataset_id"]) for row in source_evidence}
                        & {int(row["dataset_id"]) for row in target_evidence}
                    )
                    confidence = min(
                        0.99,
                        base_confidence + (0.03 if datasets_overlap else 0.0),
                    )
                    relationship_id = repository.upsert_relationship(
                        project_id=project_id,
                        source_id=object_ids[source_key],
                        target_id=object_ids[target_key],
                        relationship_type=rel_type,
                        confidence=confidence,
                        reasoning=reasoning,
                        metadata={
                            "source_candidate": source_key,
                            "target_candidate": target_key,
                            "shared_dataset_ids": datasets_overlap,
                            "inference_basis": "ONTOLOGY_RULE_AND_EVIDENCE_COOCCURRENCE",
                        },
                        run_id=run_id,
                    )
                    evidence_key = f"builder:{source_key}:{rel_type}:{target_key}"
                    repository.upsert_relationship_evidence(
                        relationship_id=relationship_id,
                        evidence_key=evidence_key,
                        score=confidence,
                        reasoning=reasoning,
                        evidence={
                            "source_evidence_count": len(source_evidence),
                            "target_evidence_count": len(target_evidence),
                            "shared_dataset_ids": datasets_overlap,
                        },
                    )
                    relationship_summaries.append({
                        "operational_relationship_id": relationship_id,
                        "source": source_key,
                        "target": target_key,
                        "relationship_type": rel_type,
                        "confidence": confidence,
                    })

                warnings = []
                if not rows:
                    warnings.append(
                        f"No column evidence was found for project {project_id} and domain {domain}."
                    )
                if rows and not candidates:
                    warnings.append(
                        "Technical evidence was found, but no supported business-object candidates were identified."
                    )

                result = {
                    "knowledge_graph_build_run_id": run_id,
                    "project_id": project_id,
                    "business_domain": domain,
                    "builder_version": self.VERSION,
                    "technical_evidence_rows": len(rows),
                    "objects_generated": len(object_summaries),
                    "relationships_generated": len(relationship_summaries),
                    "evidence_links_generated": evidence_count,
                    "objects": object_summaries,
                    "relationships": relationship_summaries,
                    "warnings": warnings,
                }
                repository.complete_run(run_id, result)
                return result

        except Exception as exc:
            if run_id is not None:
                try:
                    with engine.begin() as connection:
                        KnowledgeGraphBuilderRepository(connection).fail_run(
                            run_id, str(exc)
                        )
                except Exception:
                    pass
            raise

    def _identify_candidates(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        candidates: dict[str, dict[str, Any]] = {}
        for row in rows:
            search_text = self._normalise_search_text(row)
            for rule in RULES:
                if any(re.search(pattern, search_text) for pattern in rule.patterns):
                    candidate = candidates.setdefault(
                        rule.key, {"rule": rule, "evidence": []}
                    )
                    candidate["evidence"].append(row)
        return candidates

    @staticmethod
    def _normalise_search_text(row: dict[str, Any]) -> str:
        values = (
            row.get("column_name"),
            row.get("semantic_type"),
            row.get("business_meaning"),
            row.get("dataset_name"),
        )
        return " ".join(str(value or "") for value in values).upper().replace("-", "_")

    @staticmethod
    def _evidence_score(row: dict[str, Any]) -> float:
        semantic_confidence = float(row.get("confidence_score") or 0)
        return round(max(0.65, min(0.99, semantic_confidence or 0.78)), 4)

    def _candidate_confidence(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        values = [self._evidence_score(row) for row in rows]
        volume_bonus = min(0.08, max(0, len(rows) - 1) * 0.015)
        return round(min(0.99, sum(values) / len(values) + volume_bonus), 4)

    @staticmethod
    def _evidence_reasoning(rule: CandidateRule, row: dict[str, Any]) -> str:
        semantic = row.get("semantic_type")
        suffix = f" Semantic classification: {semantic}." if semantic else ""
        return (
            f"Column {row['dataset_name']}.{row['column_name']} contains terminology "
            f"associated with the {rule.name} business object.{suffix}"
        )

    @staticmethod
    def _stable_bigint(value: str) -> int:
        digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") & 0x7FFF_FFFF_FFFF_FFFF
