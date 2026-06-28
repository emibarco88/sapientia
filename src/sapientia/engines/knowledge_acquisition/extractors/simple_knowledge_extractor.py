"""
Module: simple_knowledge_extractor.py

Purpose:
Extracts business knowledge from document text using deterministic,
configurable rules and explainable confidence components.
"""

import re

from sapientia.config.knowledge_rules_config import KnowledgeRulesConfig
from sapientia.models.knowledge import (
    KnowledgeItem,
    KnowledgeEvidence,
    KnowledgeConfidence,
    DocumentChunk,
)


class SimpleKnowledgeExtractor:

    EXTRACTOR_NAME = "SimpleKnowledgeExtractor"

    def extract(self, chunks: list[DocumentChunk]) -> list[KnowledgeItem]:
        knowledge_items = []
        seen_items = set()

        for chunk in chunks:
            candidates = []
            candidates.extend(self._extract_definitions(chunk))
            candidates.extend(self._extract_business_rules(chunk))
            candidates.extend(self._extract_kpis(chunk))
            candidates.extend(self._extract_data_asset_references(chunk))

            for item in candidates:
                key = self._dedupe_key(item)

                if key not in seen_items:
                    knowledge_items.append(item)
                    seen_items.add(key)

        return knowledge_items

    def _extract_definitions(self, chunk: DocumentChunk) -> list[KnowledgeItem]:
        items = []

        for rule in KnowledgeRulesConfig.DEFINITION_RULES:
            for match in re.finditer(rule["pattern"], chunk.content, flags=re.IGNORECASE):
                term = match.group("term").strip()
                definition = match.group("definition").strip()

                evidence_text = match.group(0)
                confidence = self._build_confidence(
                    rule_score=rule["confidence"],
                    context_score=self._heading_context_score(chunk),
                    structure_score=80.0,
                )

                item = KnowledgeItem(
                    knowledge_type="BUSINESS_TERM",
                    name=term,
                    description=definition,
                    knowledge_json={
                        "rule_category": "BUSINESS_TERM",
                    },
                    evidence=[
                        self._build_evidence(
                            chunk=chunk,
                            evidence_text=evidence_text,
                            rule_name=rule["rule_name"],
                        )
                    ],
                    confidence=confidence,
                )

                items.append(item)

        return items

    def _extract_business_rules(self, chunk: DocumentChunk) -> list[KnowledgeItem]:
        items = []

        for sentence in self._split_sentences(chunk.content):
            lowered = sentence.lower()

            matched_keywords = [
                keyword
                for keyword in KnowledgeRulesConfig.BUSINESS_RULE_KEYWORDS
                if keyword in lowered
            ]

            if matched_keywords:
                confidence = self._build_confidence(
                    rule_score=KnowledgeRulesConfig.BUSINESS_RULE_CONFIDENCE,
                    context_score=self._heading_context_score(chunk),
                    structure_score=65.0,
                )

                items.append(
                    KnowledgeItem(
                        knowledge_type="BUSINESS_RULE",
                        name=sentence[:120],
                        description=sentence,
                        knowledge_json={
                            "rule_category": "BUSINESS_RULE",
                            "matched_keywords": matched_keywords,
                        },
                        evidence=[
                            self._build_evidence(
                                chunk=chunk,
                                evidence_text=sentence,
                                rule_name="BUSINESS_RULE_KEYWORD",
                                evidence_json={"matched_keywords": matched_keywords},
                            )
                        ],
                        confidence=confidence,
                    )
                )

        return items

    def _extract_kpis(self, chunk: DocumentChunk) -> list[KnowledgeItem]:
        items = []

        for sentence in self._split_sentences(chunk.content):
            lowered = sentence.lower()

            matched_keywords = [
                keyword
                for keyword in KnowledgeRulesConfig.KPI_KEYWORDS
                if keyword in lowered
            ]

            if matched_keywords:
                confidence = self._build_confidence(
                    rule_score=KnowledgeRulesConfig.KPI_CONFIDENCE,
                    context_score=self._heading_context_score(chunk),
                    structure_score=60.0,
                )

                items.append(
                    KnowledgeItem(
                        knowledge_type="KPI_OR_METRIC",
                        name=sentence[:120],
                        description=sentence,
                        knowledge_json={
                            "rule_category": "KPI_OR_METRIC",
                            "matched_keywords": matched_keywords,
                        },
                        evidence=[
                            self._build_evidence(
                                chunk=chunk,
                                evidence_text=sentence,
                                rule_name="KPI_KEYWORD",
                                evidence_json={"matched_keywords": matched_keywords},
                            )
                        ],
                        confidence=confidence,
                    )
                )

        return items

    def _extract_data_asset_references(self, chunk: DocumentChunk) -> list[KnowledgeItem]:
        items = []

        references = re.findall(
            KnowledgeRulesConfig.DATA_ASSET_REFERENCE_PATTERN,
            chunk.content,
        )

        for reference in references:
            confidence = self._build_confidence(
                rule_score=KnowledgeRulesConfig.DATA_ASSET_REFERENCE_CONFIDENCE,
                context_score=self._heading_context_score(chunk),
                structure_score=75.0,
            )

            items.append(
                KnowledgeItem(
                    knowledge_type="DATA_ASSET_REFERENCE",
                    name=reference,
                    description=f"Possible data asset reference: {reference}",
                    knowledge_json={
                        "rule_category": "DATA_ASSET_REFERENCE",
                    },
                    evidence=[
                        self._build_evidence(
                            chunk=chunk,
                            evidence_text=reference,
                            rule_name="DATA_ASSET_REFERENCE_PATTERN",
                        )
                    ],
                    confidence=confidence,
                )
            )

        return items

    def _build_evidence(
        self,
        chunk: DocumentChunk,
        evidence_text: str,
        rule_name: str,
        evidence_json: dict | None = None,
    ) -> KnowledgeEvidence:
        return KnowledgeEvidence(
            evidence_text=evidence_text,
            extraction_method="RULE_BASED",
            rule_name=rule_name,
            rule_version=KnowledgeRulesConfig.RULE_VERSION,
            extractor_name=self.EXTRACTOR_NAME,
            start_line_number=chunk.start_line_number,
            end_line_number=chunk.end_line_number,
            evidence_json={
                "chunk_number": chunk.chunk_number,
                "heading": chunk.heading,
                **(evidence_json or {}),
            },
        )

    def _build_confidence(
        self,
        rule_score: float,
        context_score: float,
        structure_score: float,
        frequency_score: float = 0.0,
        metadata_match_score: float = 0.0,
        semantic_match_score: float = 0.0,
    ) -> KnowledgeConfidence:
        weighted_score = round(
            (
                rule_score * 0.50
                + context_score * 0.15
                + structure_score * 0.20
                + frequency_score * 0.05
                + metadata_match_score * 0.05
                + semantic_match_score * 0.05
            ),
            4,
        )

        return KnowledgeConfidence(
            rule_score=rule_score,
            context_score=context_score,
            structure_score=structure_score,
            frequency_score=frequency_score,
            metadata_match_score=metadata_match_score,
            semantic_match_score=semantic_match_score,
            ai_validation_score=None,
            final_score=weighted_score,
            confidence_json={
                "confidence_model": "RULE_CONTEXT_STRUCTURE_V1",
                "weights": {
                    "rule_score": 0.50,
                    "context_score": 0.15,
                    "structure_score": 0.20,
                    "frequency_score": 0.05,
                    "metadata_match_score": 0.05,
                    "semantic_match_score": 0.05,
                    "ai_validation_score": "future",
                },
            },
        )

    def _heading_context_score(self, chunk: DocumentChunk) -> float:
        if not chunk.heading:
            return 40.0

        heading = chunk.heading.lower()

        if any(token in heading for token in ["glossary", "definition", "business term"]):
            return 90.0

        if any(token in heading for token in ["rule", "policy", "requirement"]):
            return 85.0

        if any(token in heading for token in ["kpi", "metric", "measure"]):
            return 85.0

        return 60.0

    def _split_sentences(self, content: str) -> list[str]:
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", content)
            if sentence.strip()
        ]

    def _dedupe_key(self, item: KnowledgeItem) -> tuple:
        return (
            item.knowledge_type,
            item.name.lower().strip(),
            (item.description or "").lower().strip(),
        )