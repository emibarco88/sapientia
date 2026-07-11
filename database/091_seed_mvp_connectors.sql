INSERT INTO ekr_connection.connector
(
    project_id,
    connector_type_id,
    connector_name,
    connector_status,
    business_domain_id,
    connection_config,
    secret_reference,
    last_discovered_at
)
SELECT
    1,
    ct.connector_type_id,
    'Snowflake Demo',
    'CONNECTED',
    bd.business_domain_id,
    jsonb_build_object(
        'database', 'SAPIENTIA_DEMO',
        'schemas', jsonb_build_array('FINANCE', 'HR', 'PROCUREMENT'),
        'warehouse', 'COMPUTE_WH',
        'role', 'ACCOUNTADMIN'
    ),
    'SNOWFLAKE_ENV_VARS',
    NOW()
FROM ekr_connection.connector_type ct
LEFT JOIN ekr_business.business_domain bd
    ON bd.domain_code = 'FINANCE'
WHERE ct.connector_code = 'SNOWFLAKE'
  AND NOT EXISTS (
      SELECT 1
      FROM ekr_connection.connector c
      WHERE c.connector_name = 'Snowflake Demo'
  );

INSERT INTO ekr_connection.connector
(
    project_id,
    connector_type_id,
    connector_name,
    connector_status,
    business_domain_id,
    connection_config,
    secret_reference,
    last_discovered_at
)
SELECT
    1,
    ct.connector_type_id,
    'Enterprise Documents',
    'CONNECTED',
    bd.business_domain_id,
    jsonb_build_object(
        'supported_file_types', jsonb_build_array('PDF'),
        'purpose', 'Knowledge extraction'
    ),
    NULL,
    NOW()
FROM ekr_connection.connector_type ct
LEFT JOIN ekr_business.business_domain bd
    ON bd.domain_code = 'FINANCE'
WHERE ct.connector_code = 'PDF'
  AND NOT EXISTS (
      SELECT 1
      FROM ekr_connection.connector c
      WHERE c.connector_name = 'Enterprise Documents'
  );

INSERT INTO ekr_connection.connector
(
    project_id,
    connector_type_id,
    connector_name,
    connector_status,
    business_domain_id,
    connection_config,
    secret_reference,
    last_discovered_at
)
SELECT
    1,
    ct.connector_type_id,
    'Local CSV Files',
    'CONNECTED',
    bd.business_domain_id,
    jsonb_build_object(
        'supported_file_types', jsonb_build_array('CSV'),
        'purpose', 'Local file discovery'
    ),
    NULL,
    NOW()
FROM ekr_connection.connector_type ct
LEFT JOIN ekr_business.business_domain bd
    ON bd.domain_code = 'FINANCE'
WHERE ct.connector_code = 'CSV'
  AND NOT EXISTS (
      SELECT 1
      FROM ekr_connection.connector c
      WHERE c.connector_name = 'Local CSV Files'
  );