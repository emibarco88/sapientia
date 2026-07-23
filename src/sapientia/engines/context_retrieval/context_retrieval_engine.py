
"""
Module: context_retrieval_engine.py

Purpose:
Builds focused Enterprise Intelligence and Enterprise Knowledge context
for Sapientia AI Advisor.

The context may contain:

- Intelligence reports
- Enterprise concepts
- Intelligence findings
- Knowledge items
- Knowledge-to-asset links
- Original document chunks

An intelligence report is no longer mandatory. This allows Sapientia to
answer grounded questions directly from acquired policies, procedures,
contracts and other enterprise documents.
"""

from __future__ import annotations

import re
from typing import Any

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.context_retrieval_repository import (
    ContextRetrievalRepository,
)


class ContextRetrievalEngine:
    """
    Retrieves focused EKR context for a business question.
    """

    STOPWORDS = {
        "what",
        "does",
        "do",
        "about",
        "the",
        "a",
        "an",
        "is",
        "are",
        "how",
        "why",
        "explain",
        "tell",
        "me",
        "based",
        "on",
        "of",
        "for",
        "in",
        "to",
        "and",
        "or",
        "with",
        "sapientia",
        "know",
        "understand",
        "domain",
        "business",
        "please",
        "could",
        "would",
        "should",
        "from",
        "this",
        "that",
        "document",
        "documents",
        "policy",
    }

    def retrieve_domain_context(
        self,
        project_id: int,
        business_domain: str,
        question: str,
    ) -> dict[str, Any]:
        normalized_domain = (
            str(business_domain)
            .strip()
            .upper()
        )

        normalized_question = (
            str(question or "")
            .strip()
        )

        if not normalized_question:
            raise ValueError(
                "A question is required."
            )

        keywords = self._extract_keywords(
            normalized_question
        )

        engine = get_engine()

        with engine.begin() as connection:
            repository = (
                ContextRetrievalRepository(
                    connection
                )
            )

            domain = repository.get_business_domain(
                project_id=project_id,
                business_domain=normalized_domain,
            )

            if not domain:
                raise ValueError(
                    "No Enterprise Knowledge or "
                    "Enterprise Intelligence context "
                    f"was found for {normalized_domain}."
                )

            latest_report = (
                repository.get_latest_report(
                    project_id=project_id,
                    business_domain=(
                        normalized_domain
                    ),
                )
            )

            concepts = repository.search_concepts(
                project_id=project_id,
                business_domain=normalized_domain,
                keywords=keywords,
            )

            findings = repository.search_findings(
                project_id=project_id,
                business_domain=normalized_domain,
                keywords=keywords,
            )

            fusion_links = (
                repository.search_fusion_links(
                    project_id=project_id,
                    business_domain=(
                        normalized_domain
                    ),
                    keywords=keywords,
                )
            )

            knowledge_items = (
                repository.search_knowledge_items(
                    project_id=project_id,
                    business_domain=(
                        normalized_domain
                    ),
                    keywords=keywords,
                )
            )

            document_chunks = (
                repository.search_document_chunks(
                    project_id=project_id,
                    business_domain=(
                        normalized_domain
                    ),
                    search_query=(
                        normalized_question
                    ),
                    keywords=keywords,
                )
            )

        fallback_context = (
            latest_report.get(
                "ai_context_json"
            )
            or {}
        )

        focused_results_exist = any(
            (
                concepts,
                findings,
                fusion_links,
                knowledge_items,
                document_chunks,
            )
        )

        fallback_used = (
            not focused_results_exist
            and bool(fallback_context)
        )

        retrieval_mode = (
            "FOCUSED_EKR_RETRIEVAL"
            if focused_results_exist
            else (
                "LATEST_INTELLIGENCE_FALLBACK"
                if fallback_used
                else "EMPTY"
            )
        )

        focused_context = {
            "retrieval_mode":
                retrieval_mode,

            "project_id":
                project_id,

            "business_domain":
                normalized_domain,

            "business_domain_name":
                domain.get(
                    "domain_name"
                ),

            "question":
                normalized_question,

            "keywords":
                keywords,

            "fallback_used":
                fallback_used,

            "latest_intelligence_report":
                self._report_context(
                    latest_report
                ),

            "relevant_enterprise_concepts":
                concepts,

            "relevant_findings":
                findings,

            "relevant_knowledge_items":
                knowledge_items,

            "relevant_knowledge_asset_links":
                fusion_links,

            # Compatibility alias for existing
            # prompt and UI consumers.
            "relevant_intelligence_links":
                fusion_links,

            "relevant_document_evidence":
                document_chunks,

            "fallback_intelligence_context":
                (
                    fallback_context
                    if fallback_used
                    else {}
                ),

            # U5/U6 AI Knowledge is always exposed when present in the
            # latest persisted intelligence report, even when focused EKR
            # retrieval also returned results.
            "enterprise_ai_knowledge":
                {
                    "enterprise_reasoning":
                        fallback_context.get("enterprise_reasoning") or {},
                    "enterprise_intelligence":
                        fallback_context.get("enterprise_intelligence") or {},
                },

            "context_statistics":
                {
                    "concepts":
                        len(concepts),

                    "findings":
                        len(findings),

                    "knowledge_items":
                        len(knowledge_items),

                    "knowledge_asset_links":
                        len(fusion_links),

                    "document_chunks":
                        len(document_chunks),

                    "has_intelligence_report":
                        bool(latest_report),
                },
        }

        if (
            not focused_results_exist
            and not fallback_context
        ):
            focused_context[
                "context_warning"
            ] = (
                "Sapientia found the business "
                "domain but no question-relevant "
                "knowledge or intelligence evidence."
            )

        return {
            "project_id":
                project_id,

            "business_domain_id":
                domain.get(
                    "business_domain_id"
                ),

            "business_domain":
                normalized_domain,

            "intelligence_report_id":
                latest_report.get(
                    "intelligence_report_id"
                ),

            "focused_context":
                focused_context,
        }

    def _extract_keywords(
        self,
        question: str,
    ) -> list[str]:
        tokens = re.findall(
            r"[A-Za-z0-9][A-Za-z0-9_\-]*",
            question.lower(),
        )

        keywords: list[str] = []

        for token in tokens:
            normalized = token.strip(
                "_-"
            )

            if len(normalized) < 2:
                continue

            if normalized in self.STOPWORDS:
                continue

            if normalized not in keywords:
                keywords.append(normalized)

        return keywords[:20]

    @staticmethod
    def _report_context(
        report: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not report:
            return None

        return {
            "intelligence_report_id":
                report.get(
                    "intelligence_report_id"
                ),

            "report_title":
                report.get(
                    "report_title"
                ),

            "summary_text":
                report.get(
                    "summary_text"
                ),

            "created_at":
                report.get(
                    "created_at"
                ),
        }
