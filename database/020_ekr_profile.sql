CREATE TABLE IF NOT EXISTS ekr_profile.dataset_profile
(
    dataset_profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id         BIGINT NOT NULL,
    row_count          BIGINT,
    column_count       INTEGER,
    duplicate_rows     BIGINT,
    profile_json       JSONB,
    profiled_at        TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_dataset_profile_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ekr_profile.dataset_profile IS
'Stores profiling results calculated at the dataset level. These metrics describe the overall characteristics and quality of a dataset regardless of its source technology.';

COMMENT ON COLUMN ekr_profile.dataset_profile.dataset_profile_id IS
'Unique identifier of the dataset profiling record.';

COMMENT ON COLUMN ekr_profile.dataset_profile.dataset_id IS
'Reference to the dataset in the Operational Metadata Model (EKR Core) that has been profiled.';

COMMENT ON COLUMN ekr_profile.dataset_profile.row_count IS
'Total number of records analysed during the profiling process.';

COMMENT ON COLUMN ekr_profile.dataset_profile.column_count IS
'Total number of columns identified in the dataset.';

COMMENT ON COLUMN ekr_profile.dataset_profile.duplicate_rows IS
'Number of duplicated records detected across the analysed dataset.';

COMMENT ON COLUMN ekr_profile.dataset_profile.profile_json IS
'Flexible JSON document containing additional dataset-level profiling metrics that do not require dedicated database columns.';

COMMENT ON COLUMN ekr_profile.dataset_profile.profiled_at IS
'Timestamp indicating when the profiling process was executed.';



CREATE TABLE IF NOT EXISTS ekr_profile.column_profile
(
    column_profile_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    column_id           BIGINT NOT NULL,

    null_count          BIGINT,
    null_percentage     NUMERIC(10,4),
    distinct_count      BIGINT,
    unique_percentage   NUMERIC(10,4),

    min_value           TEXT,
    max_value           TEXT,
    min_length          INTEGER,
    max_length          INTEGER,
    avg_length          NUMERIC(10,4),

    inferred_data_type  VARCHAR(100),

    completeness_score  NUMERIC(10,4),
    validity_score      NUMERIC(10,4),
    consistency_score   NUMERIC(10,4),
    uniqueness_score    NUMERIC(10,4),
    quality_score       NUMERIC(10,4),

    sample_values       JSONB,
    top_values          JSONB,
    pattern_summary     JSONB,
    numeric_summary     JSONB,
    date_summary        JSONB,
    boolean_summary     JSONB,
    structure_summary   JSONB,
    anomaly_summary     JSONB,
    profile_json        JSONB,

    profiled_at         TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_column_profile_column
        FOREIGN KEY (column_id)
        REFERENCES ekr_core."column"(column_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ekr_profile.column_profile IS
'Stores detailed profiling metrics for every column discovered in a dataset. These metrics support data quality assessment, semantic discovery and AI-driven metadata enrichment.';

COMMENT ON COLUMN ekr_profile.column_profile.column_profile_id IS
'Unique identifier of the column profiling record.';

COMMENT ON COLUMN ekr_profile.column_profile.column_id IS
'Reference to the column in the Operational Metadata Model (EKR Core).';

COMMENT ON COLUMN ekr_profile.column_profile.null_count IS
'Total number of NULL values detected in the analysed column.';

COMMENT ON COLUMN ekr_profile.column_profile.null_percentage IS
'Percentage of NULL values relative to the total number of analysed records.';

COMMENT ON COLUMN ekr_profile.column_profile.distinct_count IS
'Number of distinct values identified in the column.';

COMMENT ON COLUMN ekr_profile.column_profile.unique_percentage IS
'Percentage of distinct values relative to the total number of analysed records.';

COMMENT ON COLUMN ekr_profile.column_profile.min_value IS
'Minimum value identified for supported data types such as numeric and date columns.';

COMMENT ON COLUMN ekr_profile.column_profile.max_value IS
'Maximum value identified for supported data types such as numeric and date columns.';

COMMENT ON COLUMN ekr_profile.column_profile.min_length IS
'Shortest value length identified within the column.';

COMMENT ON COLUMN ekr_profile.column_profile.max_length IS
'Longest value length identified within the column.';

COMMENT ON COLUMN ekr_profile.column_profile.avg_length IS
'Average length of populated values within the column.';

COMMENT ON COLUMN ekr_profile.column_profile.inferred_data_type IS
'Data type inferred by the profiling engine based on the analysed values rather than the source system definition.';

COMMENT ON COLUMN ekr_profile.column_profile.completeness_score IS
'Data quality score measuring the percentage of populated values.';

COMMENT ON COLUMN ekr_profile.column_profile.validity_score IS
'Data quality score representing the percentage of values that conform to the inferred data type or validation rules.';

COMMENT ON COLUMN ekr_profile.column_profile.consistency_score IS
'Data quality score representing how consistently values follow the dominant format or data type.';

COMMENT ON COLUMN ekr_profile.column_profile.uniqueness_score IS
'Data quality score measuring the percentage of unique values in the column.';

COMMENT ON COLUMN ekr_profile.column_profile.quality_score IS
'Overall quality score derived from the individual data quality dimensions.';

COMMENT ON COLUMN ekr_profile.column_profile.sample_values IS
'Representative sample of distinct values extracted from the column.';

COMMENT ON COLUMN ekr_profile.column_profile.top_values IS
'Most frequently occurring values together with their occurrence counts.';

COMMENT ON COLUMN ekr_profile.column_profile.pattern_summary IS
'Summary of detected value patterns including formats, casing and character distributions.';

COMMENT ON COLUMN ekr_profile.column_profile.numeric_summary IS
'Numeric statistics such as minimum, maximum, average, sum and distribution metrics.';

COMMENT ON COLUMN ekr_profile.column_profile.date_summary IS
'Date and timestamp statistics including earliest value, latest value and date range.';

COMMENT ON COLUMN ekr_profile.column_profile.boolean_summary IS
'Boolean statistics including true and false counts and percentages.';

COMMENT ON COLUMN ekr_profile.column_profile.structure_summary IS
'Statistics describing complex structures such as arrays, nested objects and collection sizes.';

COMMENT ON COLUMN ekr_profile.column_profile.anomaly_summary IS
'Summary of detected anomalies including potential outliers, invalid values and suspicious patterns.';

COMMENT ON COLUMN ekr_profile.column_profile.profile_json IS
'Extensible JSON document containing additional profiling metrics that are not represented by dedicated columns.';

COMMENT ON COLUMN ekr_profile.column_profile.profiled_at IS
'Timestamp indicating when the column was profiled.';



CREATE TABLE IF NOT EXISTS ekr_profile.sample_data
(
    sample_data_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id     BIGINT NOT NULL,
    sample_json    JSONB NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_sample_data_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ekr_profile.sample_data IS
'Stores representative sample records extracted during profiling. Sample data assists users in understanding dataset contents without querying the original source system.';

COMMENT ON COLUMN ekr_profile.sample_data.sample_data_id IS
'Unique identifier of the stored sample data record.';

COMMENT ON COLUMN ekr_profile.sample_data.dataset_id IS
'Reference to the dataset from which the sample records were extracted.';

COMMENT ON COLUMN ekr_profile.sample_data.sample_json IS
'JSON document containing representative sample records captured during profiling.';

COMMENT ON COLUMN ekr_profile.sample_data.created_at IS
'Timestamp indicating when the sample data was stored.';



CREATE INDEX IF NOT EXISTS idx_dataset_profile_dataset
ON ekr_profile.dataset_profile(dataset_id);

CREATE INDEX IF NOT EXISTS idx_column_profile_column
ON ekr_profile.column_profile(column_id);

CREATE INDEX IF NOT EXISTS idx_sample_data_dataset
ON ekr_profile.sample_data(dataset_id);