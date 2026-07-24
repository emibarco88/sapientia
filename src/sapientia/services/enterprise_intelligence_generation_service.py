"""
Application service for the business-facing Generate Intelligence action.

The workflow runs enterprise reasoning, generates findings and
recommendations, persists AI-ready knowledge, and finally produces the
existing explainable intelligence report.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_reasoning.enterprise_reasoning_engine import (
    EnterpriseReasoningEngine,
)
from sapientia.services.enterprise_intelligence_service import (
    EnterpriseIntelligenceService,
)
from sapientia.services.enterprise_intelligence_v2_service import (
    EnterpriseIntelligenceV2Service,
)
from sapientia.services.intelligence.assessment_service import (
    EnterpriseIntelligenceAssessmentService,
)
from sapientia.services.intelligence.intelligence_object_service import (
    EnterpriseIntelligenceObjectService,
)
from sapientia.services.intelligence.assessment_evolution_service import (
    EnterpriseIntelligenceEvolutionService,
)
from sapientia.services.knowledge.enterprise_knowledge_version_service import (
    EnterpriseKnowledgeVersionService,
)
from sapientia.services.knowledge.enterprise_knowledge_evolution_service import (
    EnterpriseKnowledgeEvolutionService,
)


class EnterpriseIntelligenceGenerationService:
    def generate_domain_intelligence(
        self,
        project_id: int,
        business_domain: str,
        persist: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        normalized_domain = str(
            business_domain or ""
        ).strip().upper()

        if not normalized_domain:
            raise ValueError("A business domain is required.")

        context = self._get_domain_context(
            project_id=project_id,
            business_domain=normalized_domain,
        )

        if context["connectors"] == 0:
            raise ValueError(
                f"No Enterprise Connectors are assigned to {normalized_domain}."
            )
        if context["active_datasets"] == 0:
            raise ValueError(
                f"No active datasets are available for {normalized_domain}. "
                "Run Discover Assets first."
            )
        if context["completed_understanding"] == 0:
            raise ValueError(
                "Complete Build Understanding before generating intelligence."
            )

        knowledge_version = EnterpriseKnowledgeVersionService().resolve_current(
            project_id=project_id,
            business_domain=normalized_domain,
        )
        knowledge_evolution = EnterpriseKnowledgeEvolutionService().compare_with_previous(
            current_knowledge_version_id=int(knowledge_version["knowledge_version_id"]),
            project_id=project_id,
        )
        duplicate = self._get_duplicate_assessment_by_knowledge_version(
            project_id=project_id,
            business_domain=normalized_domain,
            knowledge_version_id=int(knowledge_version["knowledge_version_id"]),
        )

        if duplicate and not force:
            latest_version = duplicate.get("assessment_version")
            latest_id = duplicate.get("assessment_id")
            message = (
                f"No relevant knowledge changes were detected since "
                f"Assessment Version {latest_version}. "
                "A duplicate assessment and report were not created."
            )
            return {
                "status": "NO_CHANGE",
                "duplicate_prevented": True,
                "message": message,
                "project_id": project_id,
                "business_domain": normalized_domain,
                "assessment_id": latest_id,
                "assessment_version": latest_version,
                "knowledge_fingerprint": knowledge_version["knowledge_fingerprint"],
                "knowledge_version_id": knowledge_version["knowledge_version_id"],
                "knowledge_version": knowledge_version["knowledge_version"],
                "latest_assessment": duplicate,
                "knowledge_evolution": knowledge_evolution,
            }

        self._set_domain_intelligence_status(
            project_id=project_id,
            business_domain=normalized_domain,
            status="RUNNING",
            message=(
                "Analysing business dependencies, risks, opportunities "
                "and supporting evidence."
            ),
        )

        try:
            reasoning = EnterpriseReasoningEngine().analyse_domain(
                project_id=project_id,
                business_domain=normalized_domain,
            )

            intelligence = EnterpriseIntelligenceV2Service().generate(
                project_id=project_id,
                business_domain=normalized_domain,
                reasoning_run_id=reasoning["reasoning_run_id"],
            )

            report = EnterpriseIntelligenceService().generate_domain_report(
                project_id=project_id,
                business_domain=normalized_domain,
                persist=persist,
            )

            knowledge_items = self._persist_ai_knowledge(
                project_id=project_id,
                business_domain=normalized_domain,
                reasoning_run_id=reasoning["reasoning_run_id"],
                intelligence=intelligence,
            )

            findings = intelligence.get("findings") or []
            recommendations = intelligence.get("recommendations") or []

            message = (
                "Enterprise Intelligence generated successfully. "
                f"{len(findings)} insight(s) and "
                f"{len(recommendations)} recommendation(s) are ready."
            )

            self._set_domain_intelligence_status(
                project_id=project_id,
                business_domain=normalized_domain,
                status="COMPLETED",
                message=message,
            )

            generation_result = {
                "status": "COMPLETED",
                "generation_reason": "FORCED" if force else "USER_REQUESTED",
                "knowledge_fingerprint": knowledge_version["knowledge_fingerprint"],
                "knowledge_version_id": knowledge_version["knowledge_version_id"],
                "knowledge_version": knowledge_version["knowledge_version"],
                "knowledge_snapshot": knowledge_version.get("snapshot_json"),
                "knowledge_evolution": knowledge_evolution,
                "message": message,
                "project_id": project_id,
                "business_domain": normalized_domain,
                "intelligence_report_id": report.get(
                    "intelligence_report_id"
                ),
                "reasoning_run_id": reasoning.get("reasoning_run_id"),
                "enterprise_intelligence_run_id": intelligence.get(
                    "enterprise_intelligence_run_id"
                ),
                "findings_generated": len(findings),
                "recommendations_generated": len(recommendations),
                "ai_knowledge_items_persisted": knowledge_items,
                "summary_text": (
                    intelligence.get("executive_summary")
                    or report.get("summary_text")
                ),
                "reasoning": reasoning,
                "intelligence": intelligence,
                "report": report,
            }

            assessment = EnterpriseIntelligenceAssessmentService().create_from_generation(
                project_id=project_id,
                business_domain=normalized_domain,
                generation=generation_result,
            )
            generation_result["assessment_id"] = assessment.get("assessment_id")
            generation_result["assessment_version"] = assessment.get("assessment_version")
            generation_result["assessment"] = assessment

            structured_intelligence = EnterpriseIntelligenceObjectService().materialise_from_generation(
                assessment_id=int(assessment["assessment_id"]),
                project_id=project_id,
                generation=generation_result,
            )
            generation_result["structured_intelligence"] = structured_intelligence
            generation_result["assessment_evolution"] = (
                EnterpriseIntelligenceEvolutionService().compare_with_previous(
                    current_assessment_id=int(assessment["assessment_id"]),
                    project_id=project_id,
                )
            )
            return generation_result

        except Exception as exc:
            import traceback

            traceback.print_exc()

            error_message = str(exc) if str(exc) else exc.__class__.__name__

            try:
                self._set_domain_intelligence_status(
                    project_id=project_id,
                    business_domain=normalized_domain,
                    status="FAILED",
                    message=error_message[:500],
                )
            except Exception:
                # Don't hide the original exception if status update fails
                pass
            
            raise RuntimeError(
                f"Enterprise Intelligence generation failed: {error_message}"
            ) from exc




    def _get_knowledge_snapshot(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, Any]:
        """
        Build a deterministic snapshot of the domain knowledge inputs.

        The fingerprint deliberately excludes intelligence outputs, so an
        assessment run cannot make its own input snapshot appear changed.
        """
        engine = get_engine()

        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT
                        c.connector_id,
                        c.connector_type_id,
                        ct.connector_code,
                        c.connector_status,
                        cd.dataset_id,
                        cd.is_active,
                        cd.last_discovered_at,
                        cls.discovery_status,
                        cls.understanding_status,
                        cls.last_discovered_at AS lifecycle_last_discovered_at,
                        cls.last_understanding_at
                    FROM ekr_connection.connector c
                    JOIN ekr_business.business_domain bd
                      ON bd.business_domain_id = c.business_domain_id
                    JOIN ekr_connection.connector_type ct
                      ON ct.connector_type_id = c.connector_type_id
                    LEFT JOIN ekr_connection.connector_dataset cd
                      ON cd.connector_id = c.connector_id
                    LEFT JOIN ekr_connection.connector_lifecycle_state cls
                      ON cls.connector_id = c.connector_id
                    WHERE c.project_id = :project_id
                      AND UPPER(bd.domain_code) = UPPER(:business_domain)
                    ORDER BY c.connector_id, cd.dataset_id
                """),
                {
                    "project_id": project_id,
                    "business_domain": business_domain,
                },
            ).mappings().all()

        serialisable_rows: list[dict[str, Any]] = []
        changed_values: list[datetime] = []

        for row in rows:
            item = dict(row)
            for key in (
                "last_discovered_at",
                "lifecycle_last_discovered_at",
                "last_understanding_at",
            ):
                value = item.get(key)
                if isinstance(value, datetime):
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    changed_values.append(value)
                    item[key] = value.isoformat()
                elif value is not None:
                    item[key] = str(value)
            serialisable_rows.append(item)

        canonical = json.dumps(
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "knowledge_inputs": serialisable_rows,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        changed_at = max(changed_values).isoformat() if changed_values else None

        return {
            "schema_version": "1.0",
            "fingerprint": fingerprint,
            "knowledge_changed_at": changed_at,
            "connector_dataset_rows": len(serialisable_rows),
        }

    def _get_duplicate_assessment_by_knowledge_version(
        self,
        project_id: int,
        business_domain: str,
        knowledge_version_id: int,
    ) -> dict[str, Any]:
        engine = get_engine()
        with engine.connect() as connection:
            row = connection.execute(text("""
                SELECT a.assessment_id,a.assessment_version,a.assessment_status,
                       a.assessment_title,a.generated_at,a.intelligence_report_id,
                       a.assessment_json,a.knowledge_version_id,kv.knowledge_version
                FROM ekr_intelligence.enterprise_intelligence_assessment a
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id=a.business_domain_id
                LEFT JOIN ekr_knowledge.enterprise_knowledge_version kv
                  ON kv.knowledge_version_id=a.knowledge_version_id
                WHERE a.project_id=:project_id
                  AND UPPER(bd.domain_code)=UPPER(:business_domain)
                  AND a.knowledge_version_id=:knowledge_version_id
                ORDER BY a.assessment_version DESC,a.assessment_id DESC
                LIMIT 1
            """), {"project_id":project_id,"business_domain":business_domain,
                    "knowledge_version_id":knowledge_version_id}).mappings().fetchone()
        return dict(row) if row else {}

    def _persist_ai_knowledge(
        self,
        project_id: int,
        business_domain: str,
        reasoning_run_id: int,
        intelligence: dict[str, Any],
    ) -> int:
        """
        Persist findings and recommendations as active AI knowledge items.

        Existing active intelligence findings and recommendations for the
        same project and business domain are retired before the new items
        are inserted.
        """
        run_id = intelligence.get("enterprise_intelligence_run_id")

        if run_id is None:
            raise ValueError(
                "enterprise_intelligence_run_id is required to persist "
                "AI knowledge."
            )

        payloads: list[dict[str, Any]] = []

        for index, finding in enumerate(
            intelligence.get("findings") or [],
            start=1,
        ):
            enterprise_object_id = finding.get("enterprise_object_id")

            payloads.append(
                {
                    "knowledge_type": "INTELLIGENCE_FINDING",
                    "knowledge_key": (
                        f"INTELLIGENCE_FINDING:{run_id}:"
                        f"{enterprise_object_id or 'GENERAL'}:{index}"
                    ),
                    "title": (
                        finding.get("title")
                        or "Enterprise insight"
                    ),
                    "content_text": (
                        finding.get("finding_text")
                        or finding.get("description")
                        or ""
                    ),
                    "enterprise_object_id": enterprise_object_id,
                    "reasoning_run_id": reasoning_run_id,
                    "confidence_score": (
                        finding.get("confidence_score")
                        if finding.get("confidence_score") is not None
                        else 0
                    ),
                    "evidence_count": int(
                        finding.get("evidence_count") or 0
                    ),
                    "source_schema": finding.get("source_schema"),
                    "source_table": finding.get("source_table"),
                    "source_record_id": finding.get(
                        "source_record_id"
                    ),
                    "knowledge_json": finding,
                }
            )

        for index, recommendation in enumerate(
            intelligence.get("recommendations") or [],
            start=1,
        ):
            enterprise_object_id = recommendation.get(
                "enterprise_object_id"
            )

            payloads.append(
                {
                    "knowledge_type": "RECOMMENDATION",
                    "knowledge_key": (
                        f"RECOMMENDATION:{run_id}:"
                        f"{enterprise_object_id or 'GENERAL'}:{index}"
                    ),
                    "title": (
                        recommendation.get("title")
                        or "Recommendation"
                    ),
                    "content_text": (
                        recommendation.get("recommendation_text")
                        or recommendation.get("description")
                        or ""
                    ),
                    "enterprise_object_id": enterprise_object_id,
                    "reasoning_run_id": reasoning_run_id,
                    "confidence_score": (
                        recommendation.get("confidence_score")
                        if recommendation.get("confidence_score") is not None
                        else 0
                    ),
                    "evidence_count": int(
                        recommendation.get("evidence_count") or 0
                    ),
                    "source_schema": recommendation.get(
                        "source_schema"
                    ),
                    "source_table": recommendation.get(
                        "source_table"
                    ),
                    "source_record_id": recommendation.get(
                        "source_record_id"
                    ),
                    "knowledge_json": recommendation,
                }
            )

        if not payloads:
            return 0

        engine = get_engine()

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE ekr_ai.ai_knowledge_item
                    SET
                        is_active = FALSE,
                        updated_at = NOW()
                    WHERE project_id = :project_id
                      AND UPPER(business_domain) =
                          UPPER(:business_domain)
                      AND knowledge_type IN (
                          'INTELLIGENCE_FINDING',
                          'RECOMMENDATION'
                      )
                      AND is_active = TRUE
                    """
                ),
                {
                    "project_id": project_id,
                    "business_domain": business_domain,
                },
            )

            for payload in payloads:
                connection.execute(
                    text(
                        """
                        INSERT INTO ekr_ai.ai_knowledge_item
                        (
                            project_id,
                            business_domain,
                            enterprise_intelligence_run_id,
                            reasoning_run_id,
                            enterprise_object_id,
                            knowledge_type,
                            knowledge_key,
                            title,
                            content_text,
                            confidence_score,
                            evidence_count,
                            source_schema,
                            source_table,
                            source_record_id,
                            knowledge_json,
                            is_active
                        )
                        VALUES
                        (
                            :project_id,
                            :business_domain,
                            :run_id,
                            :reasoning_run_id,
                            :enterprise_object_id,
                            :knowledge_type,
                            :knowledge_key,
                            :title,
                            :content_text,
                            :confidence_score,
                            :evidence_count,
                            :source_schema,
                            :source_table,
                            :source_record_id,
                            CAST(:knowledge_json AS JSONB),
                            TRUE
                        )
                        """
                    ),
                    {
                        "project_id": project_id,
                        "business_domain": business_domain,
                        "run_id": run_id,
                        **{
                            key: value
                            for key, value in payload.items()
                            if key != "knowledge_json"
                        },
                        "knowledge_json": json.dumps(
                            payload["knowledge_json"],
                            default=str,
                        ),
                    },
                )

        return len(payloads)

    def _get_domain_context(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, int]:
        engine = get_engine()

        with engine.begin() as connection:
            domain_exists = (
                connection.execute(
                    text("""
                        SELECT 1
                        FROM ekr_business.business_domain
                        WHERE UPPER(domain_code) =
                              UPPER(:business_domain)
                    """),
                    {
                        "business_domain":
                            business_domain,
                    },
                ).scalar_one_or_none()
            )

            if not domain_exists:
                raise ValueError(
                    f"Business domain "
                    f"'{business_domain}' was not found."
                )

            row = connection.execute(
                text("""
                    SELECT
                        COUNT(
                            DISTINCT c.connector_id
                        ) AS connectors,

                        COUNT(
                            DISTINCT cd.dataset_id
                        ) FILTER (
                            WHERE cd.is_active = TRUE
                        ) AS active_datasets,

                        COUNT(
                            DISTINCT c.connector_id
                        ) FILTER (
                            WHERE cls.understanding_status =
                                  'COMPLETED'
                        ) AS completed_understanding

                    FROM ekr_connection.connector c

                    JOIN ekr_business.business_domain bd
                      ON bd.business_domain_id =
                         c.business_domain_id

                    LEFT JOIN
                        ekr_connection
                        .connector_dataset cd
                      ON cd.connector_id =
                         c.connector_id

                    LEFT JOIN
                        ekr_connection
                        .connector_lifecycle_state cls
                      ON cls.connector_id =
                         c.connector_id

                    WHERE c.project_id =
                          :project_id

                      AND UPPER(
                          bd.domain_code
                      ) = UPPER(
                          :business_domain
                      )
                """),
                {
                    "project_id":
                        project_id,

                    "business_domain":
                        business_domain,
                },
            ).mappings().one()

        return {
            "connectors":
                int(
                    row["connectors"]
                    or 0
                ),

            "active_datasets":
                int(
                    row["active_datasets"]
                    or 0
                ),

            "completed_understanding":
                int(
                    row[
                        "completed_understanding"
                    ]
                    or 0
                ),
        }

    def _set_domain_intelligence_status(
        self,
        project_id: int,
        business_domain: str,
        status: str,
        message: str,
    ) -> None:
        engine = get_engine()

        with engine.begin() as connection:
            connector_rows = (
                connection.execute(
                    text("""
                        SELECT c.connector_id

                        FROM ekr_connection.connector c

                        JOIN
                            ekr_business
                            .business_domain bd
                          ON bd.business_domain_id =
                             c.business_domain_id

                        WHERE c.project_id =
                              :project_id

                          AND UPPER(
                              bd.domain_code
                          ) = UPPER(
                              :business_domain
                          )
                    """),
                    {
                        "project_id":
                            project_id,

                        "business_domain":
                            business_domain,
                    },
                ).mappings().all()
            )

            for connector in connector_rows:
                connection.execute(
                    text("""
                        INSERT INTO
                            ekr_connection
                            .connector_lifecycle_state
                        (
                            connector_id,
                            intelligence_status,
                            intelligence_message,
                            last_intelligence_at,
                            updated_at
                        )
                        VALUES
                        (
                            :connector_id,
                            :status,
                            :message,

                            CASE
                                WHEN :status =
                                     'COMPLETED'
                                THEN NOW()
                                ELSE NULL
                            END,

                            NOW()
                        )

                        ON CONFLICT
                        (
                            connector_id
                        )
                        DO UPDATE
                        SET
                            intelligence_status =
                                EXCLUDED
                                .intelligence_status,

                            intelligence_message =
                                EXCLUDED
                                .intelligence_message,

                            last_intelligence_at =
                                CASE
                                    WHEN :status =
                                         'COMPLETED'
                                    THEN NOW()
                                    ELSE
                                        connector_lifecycle_state
                                        .last_intelligence_at
                                END,

                            updated_at =
                                NOW()
                    """),
                    {
                        "connector_id":
                            connector[
                                "connector_id"
                            ],

                        "status":
                            status,

                        "message":
                            message,
                    },
                )