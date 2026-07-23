SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'ekr_understanding'
ORDER BY table_name;

SELECT
    component_code,
    component_name,
    current_version,
    is_active
FROM ekr_runtime.runtime_component
WHERE component_code = 'ENTERPRISE_UNDERSTANDING';

SELECT
    understanding_run_id,
    project_id,
    scope_key,
    run_status,
    current_stage,
    started_at,
    completed_at,
    error_message
FROM ekr_understanding.understanding_run
ORDER BY understanding_run_id DESC
LIMIT 10;

SELECT
    understanding_snapshot_id,
    project_id,
    source_run_id,
    scope_key,
    snapshot_version,
    snapshot_status,
    object_count,
    relationship_count,
    published_at
FROM ekr_understanding.understanding_snapshot
ORDER BY understanding_snapshot_id DESC
LIMIT 10;
