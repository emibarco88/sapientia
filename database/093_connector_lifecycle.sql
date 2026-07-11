CREATE TABLE IF NOT EXISTS ekr_connection.connector_dataset
(
    connector_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    first_discovered_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    last_discovered_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    removed_from_scope_at TIMESTAMPTZ,

    CONSTRAINT pk_connector_dataset
        PRIMARY KEY
        (
            connector_id,
            dataset_id
        ),

    CONSTRAINT fk_connector_dataset_connector
        FOREIGN KEY (connector_id)
        REFERENCES ekr_connection.connector(connector_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_connector_dataset_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_connector_dataset_active
ON ekr_connection.connector_dataset
(
    connector_id,
    is_active
);


CREATE INDEX IF NOT EXISTS idx_connector_dataset_dataset
ON ekr_connection.connector_dataset
(
    dataset_id
);


CREATE TABLE IF NOT EXISTS
    ekr_connection.connector_lifecycle_state
(
    connector_id BIGINT PRIMARY KEY,

    discovery_status VARCHAR(30)
        NOT NULL DEFAULT 'PENDING',

    understanding_status VARCHAR(30)
        NOT NULL DEFAULT 'PENDING',

    intelligence_status VARCHAR(30)
        NOT NULL DEFAULT 'PENDING',

    discovery_message TEXT,
    understanding_message TEXT,
    intelligence_message TEXT,

    last_discovered_at TIMESTAMPTZ,
    last_understanding_at TIMESTAMPTZ,
    last_intelligence_at TIMESTAMPTZ,

    updated_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_connector_lifecycle_connector
        FOREIGN KEY (connector_id)
        REFERENCES ekr_connection.connector(connector_id)
        ON DELETE CASCADE
);


COMMENT ON TABLE
    ekr_connection.connector_dataset
IS
'Maintains current and historical dataset membership for an Enterprise Connector.';


COMMENT ON TABLE
    ekr_connection.connector_lifecycle_state
IS
'Tracks the latest customer-facing lifecycle status for an Enterprise Connector.';