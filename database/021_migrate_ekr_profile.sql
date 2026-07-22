BEGIN;


ALTER TABLE ekr_profile.dataset_profile
ADD COLUMN IF NOT EXISTS profiled_at
    TIMESTAMP NOT NULL DEFAULT NOW();


ALTER TABLE ekr_profile.column_profile
ADD COLUMN IF NOT EXISTS profiled_at
    TIMESTAMP NOT NULL DEFAULT NOW();


ALTER TABLE ekr_profile.dataset_sample
ADD COLUMN IF NOT EXISTS created_at
    TIMESTAMP NOT NULL DEFAULT NOW();


CREATE INDEX IF NOT EXISTS idx_dataset_profile_dataset_profiled
ON ekr_profile.dataset_profile
(
    dataset_id,
    profiled_at DESC
);


CREATE INDEX IF NOT EXISTS idx_column_profile_column_profiled
ON ekr_profile.column_profile
(
    column_id,
    profiled_at DESC
);


COMMIT;