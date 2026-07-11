"""
Module: context_retrieval_engine.py

Purpose:
Builds focused AI context from Sapientia Enterprise Intelligence.
"""

import re

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.context_retrieval_repository import (
    ContextRetrievalRepository,
)


class ContextRetrievalEngine:
    STOPWORDS = {
        "what", "does", "do", "about", "the", "a", "an", "is", "are",
        "how", "why", "explain", "tell", "me", "based", "on", "of",
        "for", "in", "to", "and", "or", "with", "sapientia", "know",
        "understand", "domain", "business",
    }

    def retrieve_domain_context(
        self,
        project_id: int,
        business_domain: str,
        question: str,
    ) -> dict:
        business_domain = business_domain.upper()
        keywords = self._extract_keywords(question)

        engine = get_engine()

        with engine.begin() as connection:
            repository = ContextRetrievalRepository(connection)

            latest_report = repository.get_latest_report(
                project_id=project_id,
                business_domain=business_domain,
            )

            if not latest_report:
                raise ValueError(
                    f"No intelligence report found for {business_domain}. "
                    "Run the intelligence command first."
                )

            concepts = repository.search_concepts(
                project_id=project_id,
                business_domain=business_domain,
                keywords=keywords,
            )

            findings = repository.search_findings(
                project_id=project_id,
                business_domain=business_domain,
                keywords=keywords,
            )

            fusion_links = repository.search_fusion_links(
                project_id=project_id,
                business_domain=business_domain,
                keywords=keywords,
            )

        fallback_context = latest_report.get("ai_context_json", {})

        focused_context = {
            "instruction": (
                "Use only this focused Sapientia Enterprise Intelligence context. "
                "Do not invent facts. If information is missing, say it is unknown."
            ),
            "retrieval_mode": "DETERMINISTIC_KEYWORD_V1",
            "question": question,
            "keywords": keywords,
            "business_domain": business_domain,
            "intelligence_report_id": latest_report.get("intelligence_report_id"),
            "domain_summary": fallback_context.get("summary", {}),
            "relevant_enterprise_concepts": concepts,
            "relevant_findings": findings,
            "relevant_intelligence_links": fusion_links,
        }

        if not concepts and not findings and not fusion_links:
            focused_context["fallback_used"] = True
            focused_context["fallback_note"] = (
                "No specific keyword matches were found, so the latest full "
                "domain AI context is included."
            )
            focused_context["domain_context"] = fallback_context
        else:
            focused_context["fallback_used"] = False

        return {
            "intelligence_report_id": latest_report.get("intelligence_report_id"),
            "business_domain_id": latest_report.get("business_domain_id"),
            "focused_context": focused_context,
        }

    def _extract_keywords(self, question: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9_]+", question.lower())

        keywords = [
            token
            for token in tokens
            if len(token) > 2 and token not in self.STOPWORDS
        ]

        expanded = set(keywords)

        for keyword in keywords:
            if keyword.endswith("s"):
                expanded.add(keyword[:-1])
            else:
                expanded.add(keyword + "s")

        return sorted(expanded) or ["finance"]