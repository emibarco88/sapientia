\set ON_ERROR_STOP on

-- Usage:
-- psql "$PSQL_URL" -v project_id=1 -v business_domain='FINANCE' \
--   -f database/verification/451_verify_u1_u4_persistence.sql

\if :{?project_id}
\else
\set project_id 1
\endif

\if :{?business_domain}
\else
\set business_domain 'FINANCE'
\endif

\echo 'Latest U1-U3 understanding runs'
SELECT
    understanding_run_id,
    project_id,
    scope_type,
    scope_reference,
    run_status,
    current_stage,
    model_version,
    requested_dataset_ids,
    objects_generated,
    relationships_generated,
    warnings_count,
    started_at,
    completed_at,
    error_message
FROM ekr_understanding.understanding_run
WHERE project_id = :project_id
  AND (
      scope_reference = :'business_domain'
      OR scope_reference IS NULL
  )
ORDER BY understanding_run_id DESC
LIMIT 12;

\echo 'Latest published U1-U3 snapshots'
SELECT
    understanding_snapshot_id,
    source_run_id,
    project_id,
    scope_type,
    scope_reference,
    snapshot_version,
    snapshot_status,
    model_version,
    object_count,
    relationship_count,
    summary_json,
    published_at
FROM ekr_understanding.understanding_snapshot
WHERE project_id = :project_id
  AND snapshot_status = 'PUBLISHED'
ORDER BY understanding_snapshot_id DESC
LIMIT 12;

\echo 'U2 persisted enterprise objects and relationships'
SELECT
    (SELECT COUNT(*)
       FROM ekr_understanding.enterprise_object
      WHERE project_id = :project_id
        AND status = 'ACTIVE') AS active_objects,
    (SELECT COUNT(*)
       FROM ekr_understanding.operational_relationship
      WHERE project_id = :project_id
        AND status = 'ACTIVE') AS active_relationships,
    (SELECT COUNT(*)
       FROM ekr_understanding.relationship_evidence re
       JOIN ekr_understanding.operational_relationship r
         ON r.operational_relationship_id = re.operational_relationship_id
      WHERE r.project_id = :project_id
        AND r.status = 'ACTIVE') AS relationship_evidence;

\echo 'U3 persisted processes'
SELECT
    (SELECT COUNT(*)
       FROM ekr_understanding.business_process
      WHERE project_id = :project_id
        AND status = 'ACTIVE') AS active_processes,
    (SELECT COUNT(*)
       FROM ekr_understanding.process_step ps
       JOIN ekr_understanding.business_process bp
         ON bp.business_process_id = ps.business_process_id
      WHERE bp.project_id = :project_id
        AND bp.status = 'ACTIVE') AS process_steps,
    (SELECT COUNT(*)
       FROM ekr_understanding.process_transition pt
       JOIN ekr_understanding.business_process bp
         ON bp.business_process_id = pt.business_process_id
      WHERE bp.project_id = :project_id
        AND bp.status = 'ACTIVE') AS process_transitions;

\echo 'U4 persisted operational contexts and facts'
SELECT
    (SELECT COUNT(*)
       FROM ekr_understanding.operational_context
      WHERE project_id = :project_id) AS operational_contexts,
    (SELECT COUNT(*)
       FROM ekr_understanding.operational_context_fact f
       JOIN ekr_understanding.operational_context c
         ON c.operational_context_id = f.operational_context_id
      WHERE c.project_id = :project_id) AS operational_context_facts;
