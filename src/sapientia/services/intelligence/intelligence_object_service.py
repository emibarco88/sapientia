"""Materialises and reads structured Enterprise Intelligence objects."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.intelligence_object_repository import (
    EnterpriseIntelligenceObjectRepository,
)


class EnterpriseIntelligenceObjectService:
    _OBJECT_TYPES = {
        "OBSERVATION", "FINDING", "RISK", "OPPORTUNITY", "KPI",
        "RECOMMENDATION", "ROOT_CAUSE", "BUSINESS_IMPACT",
    }

    def materialise_from_generation(
        self,
        assessment_id: int,
        project_id: int,
        generation: dict[str, Any],
    ) -> dict[str, Any]:
        candidates = self._extract_candidates(generation)

        engine = get_engine()
        with engine.begin() as connection:
            repository = EnterpriseIntelligenceObjectRepository(connection)
            repository.replace_assessment_objects(assessment_id)

            persisted: list[dict[str, Any]] = []
            ids_by_enterprise_object: dict[int, list[tuple[str, int]]] = {}

            for sequence, candidate in enumerate(candidates, start=1):
                candidate["sequence_number"] = sequence
                object_id = repository.create_object(assessment_id, candidate)
                candidate["intelligence_object_id"] = object_id
                persisted.append(candidate)

                enterprise_object_id = candidate.get("enterprise_object_id")
                if enterprise_object_id is not None:
                    ids_by_enterprise_object.setdefault(int(enterprise_object_id), []).append(
                        (candidate["object_type"], object_id)
                    )

                evidence_items = candidate.get("evidence") or []
                if not evidence_items and self._has_source_reference(candidate):
                    evidence_items = [self._source_evidence(candidate)]
                for evidence in evidence_items:
                    repository.create_evidence(
                        assessment_id,
                        object_id,
                        self._normalise_evidence(evidence, candidate),
                    )

            self._create_semantic_relations(repository, assessment_id, persisted, ids_by_enterprise_object)
            summary = repository.summary(assessment_id, project_id)

        return {
            **summary,
            "objects_materialised": len(persisted),
            "object_types": sorted({item["object_type"] for item in persisted}),
        }

    def list_objects(
        self,
        assessment_id: int,
        project_id: int = 1,
        object_type: str | None = None,
    ) -> list[dict[str, Any]]:
        normalised_type = object_type.upper() if object_type else None
        if normalised_type and normalised_type not in self._OBJECT_TYPES:
            raise ValueError(f"Unsupported intelligence object type: {object_type}")
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceObjectRepository(connection).list_objects(
                assessment_id, project_id, normalised_type
            )

    def get_object(self, object_id: int, project_id: int = 1) -> dict[str, Any]:
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceObjectRepository(connection).get_object(object_id, project_id)

    def summary(self, assessment_id: int, project_id: int = 1) -> dict[str, Any]:
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceObjectRepository(connection).summary(assessment_id, project_id)

    def _extract_candidates(self, generation: dict[str, Any]) -> list[dict[str, Any]]:
        intelligence = generation.get("intelligence") or {}
        reasoning = generation.get("reasoning") or {}
        report = generation.get("report") or {}
        candidates: list[dict[str, Any]] = []

        explicit_sources = {
            "OBSERVATION": [intelligence.get("observations"), report.get("observations")],
            "RISK": [intelligence.get("risks"), report.get("risks")],
            "OPPORTUNITY": [intelligence.get("opportunities"), report.get("opportunities")],
            "KPI": [intelligence.get("kpis"), report.get("kpis")],
            "ROOT_CAUSE": [intelligence.get("root_causes"), reasoning.get("root_causes")],
            "BUSINESS_IMPACT": [intelligence.get("business_impacts"), reasoning.get("impacts")],
        }
        for object_type, sources in explicit_sources.items():
            for source in sources:
                for item in self._as_dicts(source):
                    candidates.append(self._normalise_object(object_type, item, len(candidates) + 1))

        for item in self._as_dicts(intelligence.get("findings")):
            inferred_type = self._infer_finding_type(item)
            candidates.append(self._normalise_object(inferred_type, item, len(candidates) + 1))

        # The deterministic report can contain additional findings that V2 did not emit.
        for item in self._as_dicts(report.get("findings")):
            candidate = self._normalise_object("FINDING", item, len(candidates) + 1)
            if not self._candidate_exists(candidates, candidate):
                candidates.append(candidate)

        for item in self._as_dicts(intelligence.get("recommendations")):
            candidates.append(self._normalise_object("RECOMMENDATION", item, len(candidates) + 1))

        return self._deduplicate(candidates)

    @staticmethod
    def _as_dicts(value: Any) -> Iterable[dict[str, Any]]:
        if isinstance(value, dict):
            yield value
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
                elif item is not None:
                    yield {"description": str(item)}

    def _normalise_object(self, object_type: str, raw: dict[str, Any], ordinal: int) -> dict[str, Any]:
        title = self._first(
            raw, "title", "finding_title", "recommendation_title", "name", "kpi_name",
            "risk_title", "opportunity_title", "root_cause_title", "impact_title",
        ) or self._default_title(object_type, ordinal)
        description = self._first(
            raw, "description", "finding_text", "finding_description",
            "recommendation_text", "summary", "observation_text", "risk_description",
            "opportunity_description", "root_cause_text", "impact_description", "value_text",
        )
        interpretation = self._first(
            raw, "interpretation", "finding_interpretation", "reason", "rationale",
            "business_interpretation", "explanation",
        )
        enterprise_object_id = self._integer(
            self._first(raw, "enterprise_object_id", "related_enterprise_object_id")
        )
        source_object_id = self._integer(self._first(raw, "source_object_id"))

        normalised = {
            "object_type": object_type,
            "object_key": self._object_key(object_type, raw, title, ordinal),
            "title": str(title),
            "description": str(description) if description is not None else None,
            "interpretation": str(interpretation) if interpretation is not None else None,
            "status": str(raw.get("status") or "ACTIVE").upper(),
            "category": self._first(raw, "category", "finding_type", "recommendation_type", "kpi_category"),
            "severity": self._normalise_level(self._first(raw, "severity", "severity_level", "risk_level")),
            "priority": self._normalise_level(self._first(raw, "priority", "recommendation_priority")),
            "confidence_score": self._score(self._first(raw, "confidence_score", "confidence")),
            "probability_score": self._score(self._first(raw, "probability_score", "probability", "likelihood")),
            "impact_score": self._score(self._first(raw, "impact_score", "impact")),
            "estimated_value": self._number(self._first(raw, "estimated_value", "value", "financial_impact")),
            "estimated_value_currency": self._first(raw, "estimated_value_currency", "currency"),
            "enterprise_object_id": enterprise_object_id,
            "source_object_type": self._first(raw, "source_object_type"),
            "source_object_id": source_object_id,
            "source_schema": self._first(raw, "source_schema"),
            "source_table": self._first(raw, "source_table"),
            "source_record_id": self._string_or_none(self._first(raw, "source_record_id")),
            "object_json": raw,
            "evidence": list(self._as_dicts(raw.get("evidence"))),
        }
        if normalised["status"] not in {"ACTIVE", "RESOLVED", "DISMISSED", "SUPERSEDED", "RETIRED"}:
            normalised["status"] = "ACTIVE"
        return normalised

    @staticmethod
    def _infer_finding_type(item: dict[str, Any]) -> str:
        text = " ".join(str(item.get(key) or "") for key in (
            "finding_type", "title", "finding_title", "finding_text", "finding_description", "category"
        )).upper()
        if any(token in text for token in ("RISK", "VULNERAB", "EXPOSURE", "CONTROL GAP")):
            return "RISK"
        if any(token in text for token in ("OPPORTUNITY", "OPTIMIS", "IMPROVEMENT", "VALUE POTENTIAL")):
            return "OPPORTUNITY"
        if any(token in text for token in ("OBSERVATION", "DOMAIN SUMMARY", "SUMMARY")):
            return "OBSERVATION"
        return "FINDING"

    def _create_semantic_relations(
        self,
        repository: EnterpriseIntelligenceObjectRepository,
        assessment_id: int,
        objects: list[dict[str, Any]],
        ids_by_enterprise_object: dict[int, list[tuple[str, int]]],
    ) -> None:
        # Objects referring to the same canonical enterprise object are explicitly connected.
        for grouped in ids_by_enterprise_object.values():
            for source_type, source_id in grouped:
                for target_type, target_id in grouped:
                    if source_id == target_id:
                        continue
                    relation = self._relation_for(source_type, target_type)
                    if relation:
                        repository.create_relation(assessment_id, source_id, target_id, relation)

        findings = [item for item in objects if item["object_type"] in {"FINDING", "RISK", "OPPORTUNITY"}]
        recommendations = [item for item in objects if item["object_type"] == "RECOMMENDATION"]
        causes = [item for item in objects if item["object_type"] == "ROOT_CAUSE"]
        impacts = [item for item in objects if item["object_type"] == "BUSINESS_IMPACT"]

        # When explicit object identifiers are unavailable, conservative lexical matching
        # creates explainable links without inventing business facts.
        for recommendation in recommendations:
            target = self._best_text_match(recommendation, findings)
            if target:
                repository.create_relation(
                    assessment_id,
                    recommendation["intelligence_object_id"],
                    target["intelligence_object_id"],
                    "ADDRESSES",
                    recommendation.get("confidence_score"),
                    {"method": "shared_business_terms"},
                )
        for cause in causes:
            target = self._best_text_match(cause, findings)
            if target:
                repository.create_relation(
                    assessment_id,
                    cause["intelligence_object_id"],
                    target["intelligence_object_id"],
                    "ROOT_CAUSE_OF",
                    cause.get("confidence_score"),
                    {"method": "shared_business_terms"},
                )
        for impact in impacts:
            target = self._best_text_match(impact, findings)
            if target:
                repository.create_relation(
                    assessment_id,
                    impact["intelligence_object_id"],
                    target["intelligence_object_id"],
                    "IMPACT_OF",
                    impact.get("confidence_score"),
                    {"method": "shared_business_terms"},
                )

    @staticmethod
    def _relation_for(source_type: str, target_type: str) -> str | None:
        mapping = {
            ("RECOMMENDATION", "FINDING"): "ADDRESSES",
            ("RECOMMENDATION", "RISK"): "MITIGATES",
            ("ROOT_CAUSE", "FINDING"): "ROOT_CAUSE_OF",
            ("ROOT_CAUSE", "RISK"): "ROOT_CAUSE_OF",
            ("BUSINESS_IMPACT", "FINDING"): "IMPACT_OF",
            ("BUSINESS_IMPACT", "RISK"): "IMPACT_OF",
            ("KPI", "FINDING"): "MEASURES",
            ("KPI", "RISK"): "MEASURES",
        }
        return mapping.get((source_type, target_type))

    def _best_text_match(self, source: dict[str, Any], targets: list[dict[str, Any]]) -> dict[str, Any] | None:
        source_terms = self._terms(source)
        if not source_terms:
            return None
        scored = [(len(source_terms & self._terms(target)), target) for target in targets]
        score, target = max(scored, key=lambda item: item[0], default=(0, None))
        return target if score >= 1 else None

    @staticmethod
    def _terms(item: dict[str, Any]) -> set[str]:
        text = " ".join(str(item.get(key) or "") for key in ("title", "description", "interpretation"))
        stop = {"THE", "AND", "FOR", "WITH", "FROM", "THIS", "THAT", "ENTERPRISE", "BUSINESS", "RECOMMENDATION"}
        return {word for word in re.findall(r"[A-Z0-9_]+", text.upper()) if len(word) > 3 and word not in stop}

    @staticmethod
    def _normalise_evidence(evidence: dict[str, Any], owner: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_type": evidence.get("evidence_type") or "SOURCE",
            "evidence_source": evidence.get("evidence_source") or evidence.get("source"),
            "evidence_text": evidence.get("evidence_text") or evidence.get("description") or evidence.get("text"),
            "confidence_score": EnterpriseIntelligenceObjectService._score(
                evidence.get("confidence_score") if evidence.get("confidence_score") is not None else owner.get("confidence_score")
            ),
            "enterprise_object_id": EnterpriseIntelligenceObjectService._integer(
                evidence.get("enterprise_object_id") or owner.get("enterprise_object_id")
            ),
            "dataset_id": EnterpriseIntelligenceObjectService._integer(evidence.get("dataset_id")),
            "column_id": EnterpriseIntelligenceObjectService._integer(evidence.get("column_id")),
            "knowledge_item_id": EnterpriseIntelligenceObjectService._integer(evidence.get("knowledge_item_id")),
            "source_schema": evidence.get("source_schema") or owner.get("source_schema"),
            "source_table": evidence.get("source_table") or owner.get("source_table"),
            "source_record_id": EnterpriseIntelligenceObjectService._string_or_none(
                evidence.get("source_record_id") or owner.get("source_record_id")
            ),
            "evidence_json": evidence,
        }

    @staticmethod
    def _source_evidence(item: dict[str, Any]) -> dict[str, Any]:
        source = ".".join(filter(None, [item.get("source_schema"), item.get("source_table")])) or item.get("source_object_type")
        return {
            "evidence_type": "SOURCE_REFERENCE",
            "evidence_source": source,
            "evidence_text": item.get("description"),
            "confidence_score": item.get("confidence_score"),
            "enterprise_object_id": item.get("enterprise_object_id"),
            "source_schema": item.get("source_schema"),
            "source_table": item.get("source_table"),
            "source_record_id": item.get("source_record_id"),
            "evidence_json": {"derived_from_object_source": True},
        }

    @staticmethod
    def _has_source_reference(item: dict[str, Any]) -> bool:
        return any(item.get(key) is not None for key in (
            "enterprise_object_id", "source_object_id", "source_schema", "source_table", "source_record_id"
        ))

    @staticmethod
    def _candidate_exists(candidates: list[dict[str, Any]], candidate: dict[str, Any]) -> bool:
        return any(item["object_key"] == candidate["object_key"] for item in candidates)

    @staticmethod
    def _deduplicate(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in candidates:
            key = item["object_key"]
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    @staticmethod
    def _object_key(object_type: str, raw: dict[str, Any], title: str, ordinal: int) -> str:
        stable_id = EnterpriseIntelligenceObjectService._first(
            raw, "object_key", "finding_id", "recommendation_id", "risk_id",
            "opportunity_id", "kpi_id", "root_cause_id", "impact_id", "source_record_id",
        )
        basis = f"{object_type}|{stable_id or ''}|{title}|{raw.get('enterprise_object_id') or ''}"
        digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]
        return f"{object_type}:{digest}"

    @staticmethod
    def _default_title(object_type: str, ordinal: int) -> str:
        return f"{object_type.replace('_', ' ').title()} {ordinal}"

    @staticmethod
    def _first(mapping: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = mapping.get(key)
            if value not in (None, "", [], {}):
                return value
        return None

    @staticmethod
    def _score(value: Any) -> float | None:
        number = EnterpriseIntelligenceObjectService._number(value)
        if number is None:
            return None
        if number > 1:
            number /= 100
        return min(max(number, 0.0), 1.0)

    @staticmethod
    def _number(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _integer(value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalise_level(value: Any) -> str | None:
        return str(value).strip().upper()[:30] if value not in (None, "") else None

    @staticmethod
    def _string_or_none(value: Any) -> str | None:
        return str(value) if value is not None else None
