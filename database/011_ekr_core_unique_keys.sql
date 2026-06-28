ALTER TABLE ekr_core.source_system
ADD CONSTRAINT uq_source_system_project_name
UNIQUE (project_id, name);

ALTER TABLE ekr_core.dataset
ADD CONSTRAINT uq_dataset_source_location
UNIQUE (source_system_id, location);

ALTER TABLE ekr_core."column"
ADD CONSTRAINT uq_column_dataset_name_unique
UNIQUE (dataset_id, name);