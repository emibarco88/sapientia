/*
Purpose:
Registers the Sapientia AI Runtime as an executable runtime component.

This migration does not create new observability tables.
AI executions use the existing:

    ekr_runtime.runtime_execution
    ekr_runtime.runtime_execution_log
*/

INSERT INTO ekr_runtime.runtime_component
(
    component_name,
    component_code,
    component_type,
    description,
    current_version,
    is_active
)
VALUES
(
    'AI Runtime',
    'AI_RUNTIME',
    'RUNTIME',
    'Provides provider-independent AI execution for Sapientia business capabilities.',
    '1.0',
    TRUE
)
ON CONFLICT (component_code)
DO UPDATE
SET
    component_name = EXCLUDED.component_name,
    component_type = EXCLUDED.component_type,
    description = EXCLUDED.description,
    current_version = EXCLUDED.current_version,
    is_active = TRUE,
    updated_at = NOW();


COMMENT ON COLUMN ekr_runtime.runtime_execution.input_json IS
'Structured execution input metadata. Sensitive prompt content should not be stored unless explicitly required.';

COMMENT ON COLUMN ekr_runtime.runtime_execution.output_json IS
'Structured execution result metadata. AI response content should remain in its owning business repository.';


SELECT
    runtime_component_id,
    component_name,
    component_code,
    component_type,
    current_version,
    is_active
FROM ekr_runtime.runtime_component
WHERE component_code = 'AI_RUNTIME';