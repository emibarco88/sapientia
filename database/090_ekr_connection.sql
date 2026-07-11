CREATE SCHEMA IF NOT EXISTS ekr_connection;

CREATE TABLE IF NOT EXISTS ekr_connection.connector_type
(
    connector_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    connector_code    VARCHAR(100) NOT NULL UNIQUE,
    connector_name    VARCHAR(200) NOT NULL,
    connector_category VARCHAR(100) NOT NULL,
    description       TEXT,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ekr_connection.connector
(
    connector_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id          BIGINT NOT NULL,
    connector_type_id   BIGINT NOT NULL,
    connector_name      VARCHAR(300) NOT NULL,
    connector_status    VARCHAR(100) NOT NULL DEFAULT 'CONFIGURED',
    business_domain_id  BIGINT,
    connection_config   JSONB,
    secret_reference    VARCHAR(500),
    last_tested_at      TIMESTAMP,
    last_discovered_at  TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_connector_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_connector_type
        FOREIGN KEY (connector_type_id)
        REFERENCES ekr_connection.connector_type(connector_type_id),

    CONSTRAINT fk_connector_business_domain
        FOREIGN KEY (business_domain_id)
        REFERENCES ekr_business.business_domain(business_domain_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ekr_connection.connector_discovery_run
(
    connector_discovery_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    connector_id               BIGINT NOT NULL,
    project_id                 BIGINT NOT NULL,
    run_status                 VARCHAR(100) NOT NULL DEFAULT 'PENDING',
    run_message                TEXT,
    datasets_discovered        INTEGER DEFAULT 0,
    columns_discovered         INTEGER DEFAULT 0,
    started_at                 TIMESTAMP,
    completed_at               TIMESTAMP,
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_connector_discovery_connector
        FOREIGN KEY (connector_id)
        REFERENCES ekr_connection.connector(connector_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_connector_discovery_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_connector_project
ON ekr_connection.connector(project_id);

CREATE INDEX IF NOT EXISTS idx_connector_status
ON ekr_connection.connector(connector_status);

CREATE INDEX IF NOT EXISTS idx_connector_discovery_connector
ON ekr_connection.connector_discovery_run(connector_id);

INSERT INTO ekr_connection.connector_type
(
    connector_code,
    connector_name,
    connector_category,
    description
)
VALUES
('SNOWFLAKE', 'Snowflake', 'DATABASE', 'Cloud data warehouse connector for discovering databases, schemas, tables, views, columns and lineage.'),
('POSTGRESQL', 'PostgreSQL', 'DATABASE', 'Relational database connector for discovering schemas, tables, views and columns.'),
('CSV', 'CSV Files', 'FILE', 'File connector for local or uploaded CSV datasets.'),
('PDF', 'PDF Documents', 'DOCUMENT', 'Document connector for extracting enterprise knowledge from PDF files.'),
('JSON', 'JSON Files', 'FILE', 'File connector for semi-structured JSON datasets.')
ON CONFLICT (connector_code) DO NOTHING;

COMMENT ON SCHEMA ekr_connection IS
'Stores connector registry, connector configuration and discovery run metadata for Sapientia enterprise sources.';

COMMENT ON TABLE ekr_connection.connector_type IS
'Defines supported connector types such as Snowflake, PostgreSQL, CSV, PDF and JSON.';

COMMENT ON TABLE ekr_connection.connector IS
'Stores configured enterprise source connectors for a project.';

COMMENT ON TABLE ekr_connection.connector_discovery_run IS
'Stores discovery execution history for each configured connector.';