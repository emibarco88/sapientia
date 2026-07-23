\set ON_ERROR_STOP on
SELECT to_regclass('ekr_understanding.enterprise_object'),to_regclass('ekr_understanding.operational_relationship'),to_regclass('ekr_understanding.relationship_evidence'),to_regclass('ekr_understanding.snapshot_relationship');
SELECT relationship_type_code,relationship_type_name,is_active FROM ekr_understanding.relationship_type ORDER BY 1;
SELECT object_type_code,object_type_name,is_active FROM ekr_understanding.understanding_object_type WHERE object_type_code IN ('DATASET','COLUMN','KNOWLEDGE_ITEM') ORDER BY 1;
