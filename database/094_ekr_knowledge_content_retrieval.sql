ALTER TABLE ekr_knowledge.document
ADD COLUMN IF NOT EXISTS language_code VARCHAR(20);

ALTER TABLE ekr_knowledge.document
ADD COLUMN IF NOT EXISTS page_count INTEGER;

ALTER TABLE ekr_knowledge.document
ADD COLUMN IF NOT EXISTS extraction_status VARCHAR(50)
    NOT NULL DEFAULT 'COMPLETED';

ALTER TABLE ekr_knowledge.document
ADD COLUMN IF NOT EXISTS document_metadata JSONB;


ALTER TABLE ekr_knowledge.document_chunk
ADD COLUMN IF NOT EXISTS page_number INTEGER;

ALTER TABLE ekr_knowledge.document_chunk
ADD COLUMN IF NOT EXISTS character_count INTEGER;

ALTER TABLE ekr_knowledge.document_chunk
ADD COLUMN IF NOT EXISTS approximate_token_count INTEGER;

ALTER TABLE ekr_knowledge.document_chunk
ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;


ALTER TABLE ekr_knowledge.document_chunk
ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
GENERATED ALWAYS AS
(
    TO_TSVECTOR(
        'simple',
        COALESCE(heading, '')
        || ' '
        || COALESCE(content, '')
    )
)
STORED;


CREATE INDEX IF NOT EXISTS
    idx_document_chunk_search_vector
ON ekr_knowledge.document_chunk
USING GIN(search_vector);


CREATE INDEX IF NOT EXISTS
    idx_document_chunk_document_page
ON ekr_knowledge.document_chunk
(
    document_id,
    page_number,
    chunk_number
);


CREATE TABLE IF NOT EXISTS ekr_knowledge.document_summary
(
    document_summary_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    document_id BIGINT NOT NULL,

    summary_type VARCHAR(100)
        NOT NULL DEFAULT 'GENERAL',

    summary_text TEXT NOT NULL,

    generation_method VARCHAR(100)
        NOT NULL DEFAULT 'DETERMINISTIC',

    model_name VARCHAR(200),

    confidence_score NUMERIC(10,4),

    summary_json JSONB,

    created_at TIMESTAMP
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP
        NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_summary_document
        FOREIGN KEY (document_id)
        REFERENCES ekr_knowledge.document(document_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_document_summary_type
        UNIQUE
        (
            document_id,
            summary_type
        )
);


CREATE INDEX IF NOT EXISTS
    idx_document_summary_document
ON ekr_knowledge.document_summary(document_id);


COMMENT ON TABLE ekr_knowledge.document_summary IS
'Stores deterministic or AI-generated summaries of enterprise documents.';

COMMENT ON COLUMN ekr_knowledge.document_chunk.search_vector IS
'PostgreSQL full-text search vector used to retrieve document evidence for Enterprise AI context.';

COMMENT ON COLUMN ekr_knowledge.document_chunk.page_number IS
'Original document page containing this chunk when available.';

COMMENT ON COLUMN ekr_knowledge.document_chunk.chunk_metadata IS
'Extensible metadata describing extraction, chunking and provenance.';