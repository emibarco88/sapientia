\set ON_ERROR_STOP on

SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'ekr_intelligence_experience';

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'ekr_intelligence_experience'
ORDER BY table_name;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'ekr_intelligence_experience'
ORDER BY indexname;
