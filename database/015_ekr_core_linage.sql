CREATE TABLE IF NOT EXISTS ekr_core.asset_lineage
(
    asset_lineage_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id       BIGINT NOT NULL,
    lineage_type     VARCHAR(100) NOT NULL,
    source_type      VARCHAR(100) NOT NULL,
    source_name      VARCHAR(500),
    source_query     TEXT,
    lineage_json     JSONB,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_asset_lineage_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_asset_lineage_dataset
ON ekr_core.asset_lineage(dataset_id);

COMMENT ON TABLE ekr_core.asset_lineage IS
'Stores basic lineage evidence discovered for enterprise assets.';

COMMENT ON COLUMN ekr_core.asset_lineage.asset_lineage_id IS
'Primary key for the asset lineage record.';

COMMENT ON COLUMN ekr_core.asset_lineage.dataset_id IS
'Enterprise Asset associated with the lineage evidence.';

COMMENT ON COLUMN ekr_core.asset_lineage.lineage_type IS
'Type of lineage evidence, for example VIEW_DEFINITION, QUERY_HISTORY, CTAS or INSERT_SELECT.';

COMMENT ON COLUMN ekr_core.asset_lineage.source_type IS
'Technology source of the lineage evidence, for example SNOWFLAKE.';

COMMENT ON COLUMN ekr_core.asset_lineage.source_name IS
'Name of the source object, query, view or upstream object when available.';

COMMENT ON COLUMN ekr_core.asset_lineage.source_query IS
'SQL text or source statement used as lineage evidence.';

COMMENT ON COLUMN ekr_core.asset_lineage.lineage_json IS
'Structured lineage metadata captured by the connector.';

COMMENT ON COLUMN ekr_core.asset_lineage.created_at IS
'Timestamp when the lineage record was created.';