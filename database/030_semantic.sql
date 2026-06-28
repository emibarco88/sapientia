CREATE TABLE IF NOT EXISTS ekr_semantic.column_semantic
(
    column_semantic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    column_id          BIGINT NOT NULL,

    semantic_type      VARCHAR(150),
    business_meaning   VARCHAR(300),
    business_domain    VARCHAR(150),

    is_pii             BOOLEAN NOT NULL DEFAULT FALSE,
    sensitivity_level  VARCHAR(50),

    is_key_candidate   BOOLEAN NOT NULL DEFAULT FALSE,
    key_type           VARCHAR(50),

    confidence_score   NUMERIC(10,4),
    detection_method   VARCHAR(100),
    reasoning          TEXT,

    semantic_json      JSONB,

    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_column_semantic_column
        FOREIGN KEY (column_id)
        REFERENCES ekr_core."column"(column_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_column_semantic_column
        UNIQUE (column_id)
);

COMMENT ON TABLE ekr_semantic.column_semantic IS
'Stores semantic understanding inferred for each column, including business meaning, domain, PII classification, key candidates and confidence.';

COMMENT ON COLUMN ekr_semantic.column_semantic.column_semantic_id IS
'Unique identifier for the semantic classification record.';

COMMENT ON COLUMN ekr_semantic.column_semantic.column_id IS
'Reference to the column in EKR Core being semantically analysed.';

COMMENT ON COLUMN ekr_semantic.column_semantic.semantic_type IS
'Detected semantic category of the column, such as EMAIL, CUSTOMER_ID, INVOICE_ID, AMOUNT, STATUS or DATE.';

COMMENT ON COLUMN ekr_semantic.column_semantic.business_meaning IS
'Human-readable business meaning inferred for the column.';

COMMENT ON COLUMN ekr_semantic.column_semantic.business_domain IS
'Business domain inferred for the column, such as Customer, Finance, Product, Supplier or Operations.';

COMMENT ON COLUMN ekr_semantic.column_semantic.is_pii IS
'Indicates whether the column likely contains personally identifiable information.';

COMMENT ON COLUMN ekr_semantic.column_semantic.sensitivity_level IS
'Sensitivity classification such as PUBLIC, INTERNAL, CONFIDENTIAL or RESTRICTED.';

COMMENT ON COLUMN ekr_semantic.column_semantic.is_key_candidate IS
'Indicates whether the column is a candidate business key, primary key or foreign key.';

COMMENT ON COLUMN ekr_semantic.column_semantic.key_type IS
'Inferred key classification such as PRIMARY_KEY_CANDIDATE, FOREIGN_KEY_CANDIDATE or BUSINESS_KEY.';

COMMENT ON COLUMN ekr_semantic.column_semantic.confidence_score IS
'Confidence score from 0 to 100 representing how reliable the semantic inference is.';

COMMENT ON COLUMN ekr_semantic.column_semantic.detection_method IS
'Method used to infer the semantic meaning, such as RULE_BASED, PROFILE_BASED or AI_ASSISTED.';

COMMENT ON COLUMN ekr_semantic.column_semantic.reasoning IS
'Explanation of why the semantic classification was assigned.';

COMMENT ON COLUMN ekr_semantic.column_semantic.semantic_json IS
'Flexible JSON document containing additional semantic evidence, matched rules and future AI-enriched attributes.';

COMMENT ON COLUMN ekr_semantic.column_semantic.created_at IS
'Timestamp when the semantic classification was first created.';

COMMENT ON COLUMN ekr_semantic.column_semantic.updated_at IS
'Timestamp when the semantic classification was last updated.';

CREATE INDEX IF NOT EXISTS idx_column_semantic_column
ON ekr_semantic.column_semantic(column_id);

CREATE INDEX IF NOT EXISTS idx_column_semantic_type
ON ekr_semantic.column_semantic(semantic_type);

CREATE INDEX IF NOT EXISTS idx_column_semantic_domain
ON ekr_semantic.column_semantic(business_domain);

CREATE INDEX IF NOT EXISTS idx_column_semantic_pii
ON ekr_semantic.column_semantic(is_pii);